import csv
from io import StringIO

from bancobot.models import Message
from sqlmodel import Session, col, select

from classifier.models import Touchpoint


class TouchpointExporter:
    """Exporter class for Touchpoints"""

    def __init__(self, storage: Session) -> None:
        self.storage = storage

    def _get_parent_chain(self, message: Message) -> list[Message]:
        """Get all parent messages for a given message, ordered from root to immediate parent."""
        chain = []
        current = message.parent_message
        while current is not None:
            chain.insert(0, current)
            current = current.parent_message
        return chain

    def export_csv_str(self) -> StringIO:
        """Export Toucpoints into csv string.

        Each row has a event id, session id (as a case id), actor type (syste,
        AI, human), touchpoint and a timestamp. Each conversation/session/case
        has a START and END touchpoint marked as -1 and 9999, with the timestamp
        of the first and last message.

        For branched conversations, all parent touchpoints are included before
        the branched touchpoints to represent the complete conversation history.
        """
        output = StringIO()

        writer = csv.writer(output)
        headers = [
            "event_id",
            "case_id",
            "internal_id",
            "actor",
            "activity",
            "timestamp",
        ]
        writer.writerow(headers)

        # Get all touchpoints with their related messages, ordered by conversation and timestamp
        tps = self.storage.exec(
            select(Touchpoint)
            .join(Message)
            .order_by(col(Message.conversation_id), col(Message.created_at))
        ).all()

        # Group touchpoints by conversation_id (accessible through message relationship)
        grouped_messages = {}
        for tp in tps:
            conversation_id = tp.message.conversation_id
            if conversation_id not in grouped_messages:
                grouped_messages[conversation_id] = []
            grouped_messages[conversation_id].append(tp)

        i = 0
        for session_id, messages in grouped_messages.items():
            # Collect all touchpoints for this conversation (including parent chain)
            all_touchpoints = []

            # Find all parent conversations by checking if any message has a parent
            parent_conversation_ids = set()
            for tp in messages:
                parent_chain = self._get_parent_chain(tp.message)
                if parent_chain:
                    # This conversation has parent messages, so we need to include parent conversation touchpoints
                    for parent_msg in parent_chain:
                        parent_conversation_ids.add(parent_msg.conversation_id)

            # Add all touchpoints from parent conversations first
            for parent_conv_id in sorted(parent_conversation_ids):
                if parent_conv_id in grouped_messages:
                    all_touchpoints.extend(grouped_messages[parent_conv_id])

            # Add current conversation touchpoints
            all_touchpoints.extend(messages)

            # Start touchpoint (from the earliest message)
            writer.writerow(
                [
                    i,
                    session_id,
                    -1,
                    "System",
                    "START-DIALOGUE-SYSTEM",
                    all_touchpoints[0].timestamp.isoformat(),
                ]
            )
            i += 1

            # Write all touchpoints
            for internal_id, tp in enumerate(all_touchpoints):
                writer.writerow(
                    [
                        i,
                        session_id,
                        internal_id,
                        tp.message.type,
                        tp.activity,
                        tp.timestamp.isoformat(),
                    ]
                )
                i += 1

            # End touchpoint
            writer.writerow(
                [
                    i,
                    session_id,
                    99999,
                    "System",
                    "END - DIALOGUE - SYSTEM",
                    all_touchpoints[-1].timestamp.isoformat(),
                ]
            )
            i += 1
        return output
