import csv
import datetime as dt
import io
import uuid

from bancobot.models import Conversation, MessageType
from classifier.models import Touchpoint
from exporter.service import TouchpointExporter


def _read_csv(text: str) -> tuple[list[str], list[dict[str, str]]]:
    buf = io.StringIO(text)
    reader = csv.DictReader(buf)
    assert reader.fieldnames is not None
    return list(reader.fieldnames), list(reader)


class TestTouchpointExporter:
    def test_export_csv_str_basic_includes_start_end_and_catalyst_fields(
        self, db_session, make_message, fixed_dt
    ):
        catalyst_conv_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        target_conv_id = uuid.UUID("00000000-0000-0000-0000-000000000002")

        catalyst_msg_id = uuid.UUID("00000000-0000-0000-0000-0000000000a1")
        target_msg_id = uuid.UUID("00000000-0000-0000-0000-0000000000b1")

        catalyst_conv = Conversation(id=catalyst_conv_id, meta={})
        target_conv = Conversation(
            id=target_conv_id,
            meta={
                "bot_label": "my-bot",
                "catalyst_message_id": str(catalyst_msg_id),
            },
        )

        catalyst_msg = make_message(
            conversation_id=catalyst_conv_id,
            message_id=catalyst_msg_id,
            content="catalyst message",
            msg_type=MessageType.Human,
            seconds_offset=10,
        )
        target_msg = make_message(
            conversation_id=target_conv_id,
            message_id=target_msg_id,
            content="hello",
            msg_type=MessageType.AI,
            seconds_offset=20,
        )

        catalyst_tp = Touchpoint(message_id=catalyst_msg_id, activity="CATALYST_TP")
        target_tp = Touchpoint(message_id=target_msg_id, activity="TARGET_TP")

        db_session.add(catalyst_conv)
        db_session.add(target_conv)
        db_session.add(catalyst_msg)
        db_session.add(target_msg)
        db_session.add(catalyst_tp)
        db_session.add(target_tp)
        db_session.commit()

        exporter = TouchpointExporter(storage=db_session)
        csv_io = exporter.export_csv_str()

        header, rows = _read_csv(csv_io.getvalue())

        assert header == [
            "event_id",
            "case_id",
            "internal_id",
            "actor",
            "activity",
            "timestamp",
            "bot_label",
            "tool_source",
            "catalyst_case_id",
            "catalyst_message_id",
            "catalyst_message_content",
            "catalyst_activity",
            "catalyst_message_ts",
        ]

        # Only validate rows for the target conversation.
        target_rows = [r for r in rows if r["case_id"] == str(target_conv_id)]
        assert len(target_rows) == 3  # START + 1 touchpoint + END

        start, tp_row, end = target_rows

        assert start["event_id"] == "3"  # after catalyst conversation export (0,1,2)
        assert start["internal_id"] == "-1"
        assert start["actor"] == "System"
        assert start["activity"] == "START-DIALOGUE-SYSTEM"

        # Timestamp expectations: start == first touchpoint timestamp in the exported case
        assert start["timestamp"] == (fixed_dt + dt.timedelta(seconds=20)).isoformat()

        assert tp_row["event_id"] == "4"
        assert tp_row["internal_id"] == "0"
        assert tp_row["actor"] == "ai"
        assert tp_row["activity"] == "TARGET_TP"
        assert tp_row["timestamp"] == (fixed_dt + dt.timedelta(seconds=20)).isoformat()

        assert end["event_id"] == "5"
        assert end["internal_id"] == "99999"
        assert end["actor"] == "System"
        assert end["activity"] == "END - DIALOGUE - SYSTEM"
        assert end["timestamp"] == (fixed_dt + dt.timedelta(seconds=20)).isoformat()

        # Catalyst fields should be populated for *all* rows in the target conversation.
        for row in target_rows:
            assert row["bot_label"] == "my-bot"
            assert row["catalyst_case_id"] == str(catalyst_conv_id)
            assert row["catalyst_message_id"] == str(catalyst_msg_id)
            assert row["catalyst_message_content"] == "catalyst message"
            assert row["catalyst_activity"] == "CATALYST_TP"
            assert (
                row["catalyst_message_ts"]
                == (fixed_dt + dt.timedelta(seconds=10)).isoformat()
            )

    def test_export_csv_str_includes_parent_chain_for_branched_conversation(
        self, db_session, make_message, fixed_dt
    ):
        parent_conv_id = uuid.UUID("00000000-0000-0000-0000-000000000010")
        child_conv_id = uuid.UUID("00000000-0000-0000-0000-000000000020")

        parent_msg_id = uuid.UUID("00000000-0000-0000-0000-0000000000c1")
        child_msg_id = uuid.UUID("00000000-0000-0000-0000-0000000000c2")

        parent_conv = Conversation(id=parent_conv_id, meta={})
        child_conv = Conversation(id=child_conv_id, meta={"bot_label": "bot"})

        parent_msg = make_message(
            conversation_id=parent_conv_id,
            message_id=parent_msg_id,
            content="root",
            msg_type=MessageType.Human,
            seconds_offset=1,
        )
        child_msg = make_message(
            conversation_id=child_conv_id,
            message_id=child_msg_id,
            content="branch",
            msg_type=MessageType.AI,
            seconds_offset=2,
            parent_message_id=parent_msg_id,
        )
        # Ensure the relationship is available without relying on lazy-loading.
        child_msg.parent_message = parent_msg

        # Add both touchpoints.
        parent_tp = Touchpoint(message_id=parent_msg_id, activity="PARENT")
        child_tp = Touchpoint(message_id=child_msg_id, activity="CHILD")

        db_session.add(parent_conv)
        db_session.add(child_conv)
        db_session.add(parent_msg)
        db_session.add(child_msg)
        db_session.add(parent_tp)
        db_session.add(child_tp)
        db_session.commit()

        exporter = TouchpointExporter(storage=db_session)
        header, rows = _read_csv(exporter.export_csv_str().getvalue())

        child_rows = [r for r in rows if r["case_id"] == str(child_conv_id)]
        assert [r["activity"] for r in child_rows] == [
            "START-DIALOGUE-SYSTEM",
            "PARENT",
            "CHILD",
            "END - DIALOGUE - SYSTEM",
        ]

        # Internal ids should reflect the full exported history (including parents)
        assert [r["internal_id"] for r in child_rows] == ["-1", "0", "1", "99999"]

        # START timestamp should be the first included touchpoint (parent)
        assert (
            child_rows[0]["timestamp"]
            == (fixed_dt + dt.timedelta(seconds=1)).isoformat()
        )
        # END timestamp should be the last included touchpoint (child)
        assert (
            child_rows[-1]["timestamp"]
            == (fixed_dt + dt.timedelta(seconds=2)).isoformat()
        )
