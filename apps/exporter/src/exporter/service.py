import csv
import datetime as dt
import uuid
from io import StringIO
from typing import Dict, TypedDict

from bancobot.models import Conversation, Message
from classifier.models import Touchpoint
from sqlmodel import Session, col, select


class TouchpointExportFormat(TypedDict):
    """Defines the format of the exported touchpoint data."""

    event_id: int  # touchpoint id
    case_id: uuid.UUID  # conversation id
    internal_id: int  # id within the conversation
    actor: str  # SYSTEM | AI | Human
    activity: str  # touchpoint type
    timestamp: str  # simulated timestamp
    bot_label: str  # label of the bot
    tool_source: str  # source of the RAG tool used

    # if tp is a simulation.
    catalyst_case_id: (
        uuid.UUID | None  # id of the original
    )
    catalyst_message_id: uuid.UUID | None  # id of the catalyst message
    catalyst_activity: str | None  # tp of the catalyst
    catalyst_message_ts: str | None  # timestamp of the catalyst


class TouchpointExporter:
    """Exporter class for Touchpoints"""

    def __init__(self, storage: Session) -> None:
        self.storage = storage

    def _get_parent_chain(self, message: Message) -> list[Message]:
        """Get all parent messages for a given message, ordered from root to immediate parent."""
        chain: list[Message] = []
        current = message.parent_message
        while current is not None:
            chain.insert(0, current)
            current = current.parent_message
        return chain

    def export_csv_str(self) -> StringIO:
        """Export Touchpoints into a CSV string.

        Each conversation/session/case has a START and END touchpoint marked as
        internal ids -1 and 99999 respectively. For branched conversations, the
        exported case includes all parent touchpoints before the branched ones
        to represent the complete conversation history.
        """

        output = StringIO()

        writer = csv.DictWriter(
            output, fieldnames=list(TouchpointExportFormat.__annotations__.keys())
        )
        writer.writeheader()

        # Load all touchpoints, ordered by conversation and message creation time.
        # (We use Message.created_at for deterministic ordering; timestamps come from
        # touchpoint.timestamp which is based on simulated time.)
        tps = self.storage.exec(
            select(Touchpoint)
            .join(Message)
            .order_by(col(Message.conversation_id), col(Message.created_at))
        ).all()

        # Build a lookup so we can include parent-chain touchpoints cheaply.
        tp_by_message_id: dict[uuid.UUID, Touchpoint] = {
            tp.message_id: tp for tp in tps
        }

        # Group touchpoints by conversation_id
        grouped: Dict[uuid.UUID, list[Touchpoint]] = {}
        for tp in tps:
            conv_id = tp.message.conversation_id
            grouped.setdefault(conv_id, []).append(tp)

        event_id = 0
        for case_id, conv_touchpoints in grouped.items():
            conversation = self.storage.exec(
                select(Conversation).where(Conversation.id == case_id)
            ).one()
            conv_metadata = conversation.meta or {}

            # Build an ordered, de-duplicated list of touchpoints for this exported case,
            # including all parent-chain touchpoints.
            ordered_touchpoints: list[Touchpoint] = []
            seen_message_ids: set[uuid.UUID] = set()

            def _add_tp(tp: Touchpoint) -> None:
                if tp.message_id in seen_message_ids:
                    return
                ordered_touchpoints.append(tp)
                seen_message_ids.add(tp.message_id)

            # If this is a forked conversation, legacy datasets store the branch point
            # as `branched_message_id` and newer ones may use `catalyst_message_id`.
            branch_message_id = conv_metadata.get(
                "catalyst_message_id"
            ) or conv_metadata.get("branched_message_id")
            if isinstance(branch_message_id, str):
                try:
                    branch_message_id = uuid.UUID(branch_message_id)
                except ValueError:
                    branch_message_id = None

            # Seed with parent conversation touchpoints up to the branch point.
            if isinstance(branch_message_id, uuid.UUID):
                branch_tp = tp_by_message_id.get(branch_message_id)
                if branch_tp is not None:
                    parent_conv_id = branch_tp.message.conversation_id
                    for parent_tp in grouped.get(parent_conv_id, []):
                        _add_tp(parent_tp)
                        if parent_tp.message_id == branch_message_id:
                            break

            for tp in conv_touchpoints:
                for parent_msg in self._get_parent_chain(tp.message):
                    parent_tp = tp_by_message_id.get(parent_msg.id)
                    if parent_tp is None:
                        continue
                    _add_tp(parent_tp)

                _add_tp(tp)

            if not ordered_touchpoints:
                continue

            # Forked conversations in this repo have used different metadata keys over time.
            # Support both current and legacy ones.
            bot_label = conv_metadata.get("twinbot_type", "")
            tool_source = conv_metadata.get("tool_source", "")

            catalyst_case_id: uuid.UUID | None = None
            catalyst_msg_id: uuid.UUID | None = None
            catalyst_activity: str | None = None
            catalyst_message_ts: str | None = None

            catalyst_message_id = branch_message_id

            if isinstance(catalyst_message_id, uuid.UUID):
                catalyst_message = self.storage.get(Message, catalyst_message_id)
                catalyst_tp = tp_by_message_id.get(catalyst_message_id)
                if catalyst_tp is None:
                    catalyst_tp = self.storage.exec(
                        select(Touchpoint).where(
                            Touchpoint.message_id == catalyst_message_id
                        )
                    ).first()

                if catalyst_message is not None and catalyst_tp is not None:
                    catalyst_case_id = catalyst_message.conversation_id
                    catalyst_msg_id = catalyst_message.id
                    catalyst_activity = catalyst_tp.activity

                    sim_ts = catalyst_message.timing_metadata.get("simulated_timestamp")
                    catalyst_message_ts = (
                        dt.datetime.fromtimestamp(sim_ts).isoformat()
                        if sim_ts is not None
                        else catalyst_message.created_at.isoformat()
                    )

            common: dict = {
                "case_id": case_id,
                "bot_label": bot_label,
                "tool_source": tool_source,
                "catalyst_case_id": catalyst_case_id,
                "catalyst_message_id": catalyst_msg_id,
                "catalyst_activity": catalyst_activity,
                "catalyst_message_ts": catalyst_message_ts,
            }

            # START
            writer.writerow(
                {
                    "event_id": event_id,
                    "internal_id": -1,
                    "actor": "System",
                    "activity": "START-DIALOGUE-SYSTEM",
                    "timestamp": ordered_touchpoints[0].timestamp.isoformat(),
                    **common,
                }
            )
            event_id += 1

            # Touchpoints
            for internal_id, tp in enumerate(ordered_touchpoints):
                writer.writerow(
                    {
                        "event_id": event_id,
                        "internal_id": internal_id,
                        "actor": tp.message.type.value,
                        "activity": tp.activity,
                        "timestamp": tp.timestamp.isoformat(),
                        **common,
                    }
                )
                event_id += 1

            # END
            writer.writerow(
                {
                    "event_id": event_id,
                    "internal_id": 99999,
                    "actor": "System",
                    "activity": "END-DIALOGUE-SYSTEM",
                    "timestamp": ordered_touchpoints[-1].timestamp.isoformat(),
                    **common,
                }
            )
            event_id += 1

        return output
