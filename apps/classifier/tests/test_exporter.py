import datetime as dt
import uuid
from io import StringIO

from bancobot.models import Conversation, Message, MessageType
from classifier.exporter import TouchpointExporter
from classifier.models import Touchpoint


class TestTouchpointExporterInit:
    """Test TouchpointExporter initialization."""

    def test_exporter_initialization(self, db_session):
        """Test exporter initialization with session."""
        exporter = TouchpointExporter(db_session)
        assert exporter is not None
        assert exporter.storage == db_session


class TestExportCsvStr:
    """Test CSV export functionality."""

    def test_export_empty_touchpoints(self, db_session):
        """Test exporting when no touchpoints exist."""
        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        assert isinstance(result, StringIO)
        content = result.getvalue()
        lines = content.strip().split("\n")
        assert len(lines) == 1  # Only headers
        assert "event_id" in lines[0]

    def test_export_single_touchpoint(self, db_session, sample_conversation):
        """Test exporting a single touchpoint."""
        now = dt.datetime.now()
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=sample_conversation.id,
            content="Test message",
            type=MessageType.Human,
            timing_metadata={
                "simulated_timestamp": now.timestamp(),
                "pause_time": 0.0,
                "typing_time": 0.0,
                "thinking_time": 0.0,
            },
            created_at=now,
        )
        db_session.add(msg)
        db_session.commit()

        tp = Touchpoint(
            message_id=msg.id,
            message=msg,
            activity="TEST_ACTIVITY",
            created_at=now,
        )
        db_session.add(tp)
        db_session.commit()

        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        content = result.getvalue()
        lines = content.strip().split("\n")
        # Header + START + 1 touchpoint + END
        assert len(lines) == 4
        assert "START-DIALOGUE-SYSTEM" in content

    def test_export_csv_headers(self, db_session, sample_conversation):
        """Test that CSV has correct headers."""
        now = dt.datetime.now()
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=sample_conversation.id,
            content="Test message",
            type=MessageType.Human,
            timing_metadata={
                "simulated_timestamp": now.timestamp(),
                "pause_time": 0.0,
                "typing_time": 0.0,
                "thinking_time": 0.0,
            },
            created_at=now,
        )
        db_session.add(msg)
        db_session.commit()

        tp = Touchpoint(
            message_id=msg.id,
            message=msg,
            activity="TEST_ACTIVITY",
            created_at=now,
        )
        db_session.add(tp)
        db_session.commit()

        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        content = result.getvalue()
        headers = content.split("\n")[0]
        assert "event_id" in headers
        assert "case_id" in headers
        assert "internal_id" in headers
        assert "actor" in headers
        assert "activity" in headers
        assert "timestamp" in headers

    def test_export_multiple_touchpoints_same_conversation_no_branches(
        self, db_session, sample_conversation
    ):
        """Test exporting multiple touchpoints in same conversation with no branches."""
        now = dt.datetime.now()

        # Create 3 sequential messages in one conversation (no branching)
        messages = []
        for i in range(3):
            msg = Message(
                id=uuid.uuid4(),
                conversation_id=sample_conversation.id,
                content=f"Message {i}",
                type=MessageType.Human if i % 2 == 0 else MessageType.AI,
                timing_metadata={
                    "simulated_timestamp": (now + dt.timedelta(seconds=i)).timestamp(),
                    "pause_time": 0.0,
                    "typing_time": 0.0,
                    "thinking_time": 0.0,
                },
                created_at=now + dt.timedelta(seconds=i),
            )
            db_session.add(msg)
            messages.append(msg)

        db_session.commit()

        # Create touchpoints for each message
        for i, msg in enumerate(messages):
            tp = Touchpoint(
                message_id=msg.id,
                message=msg,
                activity=f"ACTIVITY_{i}",
                created_at=now + dt.timedelta(seconds=i),
            )
            db_session.add(tp)

        db_session.commit()

        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        content = result.getvalue()
        lines = content.strip().split("\n")
        # Header + START + 3 touchpoints + END
        assert len(lines) == 6

    def test_export_multiple_conversations_no_branches(self, db_session):
        """Test exporting touchpoints from multiple independent conversations."""
        now = dt.datetime.now()

        for session_num in range(2):
            conversation = Conversation(
                id=uuid.uuid4(),
                meta={},
                created_at=now,
            )
            db_session.add(conversation)
            db_session.commit()

            for msg_num in range(2):
                msg = Message(
                    id=uuid.uuid4(),
                    conversation_id=conversation.id,
                    content=f"Message {msg_num}",
                    type=MessageType.Human,
                    timing_metadata={
                        "simulated_timestamp": (
                            now + dt.timedelta(seconds=msg_num)
                        ).timestamp(),
                        "pause_time": 0.0,
                        "typing_time": 0.0,
                        "thinking_time": 0.0,
                    },
                    created_at=now + dt.timedelta(seconds=msg_num),
                )
                db_session.add(msg)
                db_session.commit()

                tp = Touchpoint(
                    message_id=msg.id,
                    message=msg,
                    activity="TEST",
                    created_at=now + dt.timedelta(seconds=msg_num),
                )
                db_session.add(tp)

        db_session.commit()

        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        content = result.getvalue()
        lines = content.strip().split("\n")
        # Header + (START + 2 touchpoints + END) * 2 conversations = 1 + (4 * 2) = 9
        assert len(lines) == 9

    def test_export_branched_conversation_single_branch(
        self, db_session, sample_conversation
    ):
        """Test exporting a branched conversation with a single branch point.

        Structure:
        - Parent conversation: msg0 -> msg1 -> msg2
        - Child conversation: inherits msg0->msg1->msg2, then adds msg3->msg4
        """
        now = dt.datetime.now()

        # Create parent conversation messages
        parent_msgs = []
        for i in range(3):
            msg = Message(
                id=uuid.uuid4(),
                conversation_id=sample_conversation.id,
                content=f"Parent message {i}",
                type=MessageType.Human if i % 2 == 0 else MessageType.AI,
                timing_metadata={
                    "simulated_timestamp": (now + dt.timedelta(seconds=i)).timestamp(),
                    "pause_time": 0.0,
                    "typing_time": 0.0,
                    "thinking_time": 0.0,
                },
                created_at=now + dt.timedelta(seconds=i),
            )
            db_session.add(msg)
            parent_msgs.append(msg)

        db_session.commit()

        # Create parent conversation touchpoints
        for i, msg in enumerate(parent_msgs):
            tp = Touchpoint(
                message_id=msg.id,
                message=msg,
                activity=f"PARENT_ACTIVITY_{i}",
                created_at=now + dt.timedelta(seconds=i),
            )
            db_session.add(tp)

        db_session.commit()

        # Create child conversation that branches from parent_msgs[2]
        child_conversation = Conversation(
            id=uuid.uuid4(),
            meta={},
            created_at=now + dt.timedelta(seconds=3),
        )
        db_session.add(child_conversation)
        db_session.commit()

        # Create branched messages (parent_msgs[2] is the parent of first child message)
        child_msgs = []
        for i in range(2):
            msg = Message(
                id=uuid.uuid4(),
                conversation_id=child_conversation.id,
                content=f"Child message {i}",
                type=MessageType.AI if i % 2 == 0 else MessageType.Human,
                parent_message_id=parent_msgs[2].id if i == 0 else None,
                timing_metadata={
                    "simulated_timestamp": (
                        now + dt.timedelta(seconds=3 + i)
                    ).timestamp(),
                    "pause_time": 0.0,
                    "typing_time": 0.0,
                    "thinking_time": 0.0,
                },
                created_at=now + dt.timedelta(seconds=3 + i),
            )
            db_session.add(msg)
            child_msgs.append(msg)

        db_session.commit()

        # Create child conversation touchpoints
        for i, msg in enumerate(child_msgs):
            tp = Touchpoint(
                message_id=msg.id,
                message=msg,
                activity=f"CHILD_ACTIVITY_{i}",
                created_at=now + dt.timedelta(seconds=3 + i),
            )
            db_session.add(tp)

        db_session.commit()

        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        content = result.getvalue()
        lines = content.strip().split("\n")

        # Parent conversation: START + 3 parent msgs + END = 5 lines
        # Child conversation: START + 3 parent msgs (from chain) + 2 child msgs + END = 7 lines
        # Total: 1 (header) + 5 (parent) + 7 (child) = 13 lines
        assert len(lines) == 13

        # Verify parent touchpoints are included in child export
        assert "PARENT_ACTIVITY_0" in content
        assert "PARENT_ACTIVITY_1" in content
        assert "PARENT_ACTIVITY_2" in content
        assert "CHILD_ACTIVITY_0" in content
        assert "CHILD_ACTIVITY_1" in content

    def test_export_branched_conversation_multiple_branches(
        self, db_session, sample_conversation
    ):
        """Test exporting multiple branched conversations from the same parent.

        Structure:
        - Parent conversation: msg0 -> msg1 -> msg2
        - Child conversation 1: inherits msg0->msg1->msg2, then adds msg3
        - Child conversation 2: inherits msg0->msg1->msg2, then adds msg4
        """
        now = dt.datetime.now()

        # Create parent conversation messages
        parent_msgs = []
        for i in range(3):
            msg = Message(
                id=uuid.uuid4(),
                conversation_id=sample_conversation.id,
                content=f"Parent message {i}",
                type=MessageType.Human if i % 2 == 0 else MessageType.AI,
                timing_metadata={
                    "simulated_timestamp": (now + dt.timedelta(seconds=i)).timestamp(),
                    "pause_time": 0.0,
                    "typing_time": 0.0,
                    "thinking_time": 0.0,
                },
                created_at=now + dt.timedelta(seconds=i),
            )
            db_session.add(msg)
            parent_msgs.append(msg)

        db_session.commit()

        # Create parent conversation touchpoints
        for i, msg in enumerate(parent_msgs):
            tp = Touchpoint(
                message_id=msg.id,
                message=msg,
                activity=f"PARENT_ACTIVITY_{i}",
                created_at=now + dt.timedelta(seconds=i),
            )
            db_session.add(tp)

        db_session.commit()

        # Create two child conversations that branch from parent_msgs[2]
        for branch_num in range(2):
            child_conversation = Conversation(
                id=uuid.uuid4(),
                meta={},
                created_at=now + dt.timedelta(seconds=3 + branch_num),
            )
            db_session.add(child_conversation)
            db_session.commit()

            # Create one branched message for each child
            msg = Message(
                id=uuid.uuid4(),
                conversation_id=child_conversation.id,
                content=f"Branch {branch_num} message",
                type=MessageType.AI,
                parent_message_id=parent_msgs[2].id,
                timing_metadata={
                    "simulated_timestamp": (
                        now + dt.timedelta(seconds=3 + branch_num)
                    ).timestamp(),
                    "pause_time": 0.0,
                    "typing_time": 0.0,
                    "thinking_time": 0.0,
                },
                created_at=now + dt.timedelta(seconds=3 + branch_num),
            )
            db_session.add(msg)
            db_session.commit()

            # Create touchpoint for child message
            tp = Touchpoint(
                message_id=msg.id,
                message=msg,
                activity=f"BRANCH_{branch_num}_ACTIVITY",
                created_at=now + dt.timedelta(seconds=3 + branch_num),
            )
            db_session.add(tp)

        db_session.commit()

        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        content = result.getvalue()
        lines = content.strip().split("\n")

        # Parent: START + 3 parent msgs + END = 5 lines
        # Child 1: START + 3 parent msgs (from chain) + 1 child msg + END = 6 lines
        # Child 2: START + 3 parent msgs (from chain) + 1 child msg + END = 6 lines
        # Total: 1 (header) + 5 + 6 + 6 = 18 lines
        assert len(lines) == 18

        # Verify both branches include parent touchpoints
        assert "PARENT_ACTIVITY_0" in content
        assert "PARENT_ACTIVITY_1" in content
        assert "PARENT_ACTIVITY_2" in content
        assert "BRANCH_0_ACTIVITY" in content
        assert "BRANCH_1_ACTIVITY" in content

    def test_export_deep_branch_chain(self, db_session, sample_conversation):
        """Test exporting deeply nested branched conversations.

        Structure:
        - Conversation 1: msg0 -> msg1
        - Conversation 2: inherits msg0->msg1, then adds msg2 (parent=msg1)
        - Conversation 3: inherits msg0->msg1->msg2, then adds msg3 (parent=msg2)
        """
        now = dt.datetime.now()

        # Create first conversation messages
        msgs_conv1 = []
        for i in range(2):
            msg = Message(
                id=uuid.uuid4(),
                conversation_id=sample_conversation.id,
                content=f"Conv1 message {i}",
                type=MessageType.Human,
                timing_metadata={
                    "simulated_timestamp": (now + dt.timedelta(seconds=i)).timestamp(),
                    "pause_time": 0.0,
                    "typing_time": 0.0,
                    "thinking_time": 0.0,
                },
                created_at=now + dt.timedelta(seconds=i),
            )
            db_session.add(msg)
            msgs_conv1.append(msg)

        db_session.commit()

        # Create touchpoints for conv1
        for i, msg in enumerate(msgs_conv1):
            tp = Touchpoint(
                message_id=msg.id,
                message=msg,
                activity=f"CONV1_ACTIVITY_{i}",
                created_at=now + dt.timedelta(seconds=i),
            )
            db_session.add(tp)

        db_session.commit()

        # Create second conversation (branches from msg1 of conv1)
        conv2 = Conversation(
            id=uuid.uuid4(),
            meta={},
            created_at=now + dt.timedelta(seconds=2),
        )
        db_session.add(conv2)
        db_session.commit()

        msg_conv2 = Message(
            id=uuid.uuid4(),
            conversation_id=conv2.id,
            content="Conv2 message",
            type=MessageType.AI,
            parent_message_id=msgs_conv1[1].id,  # Branch from last msg of conv1
            timing_metadata={
                "simulated_timestamp": (now + dt.timedelta(seconds=2)).timestamp(),
                "pause_time": 0.0,
                "typing_time": 0.0,
                "thinking_time": 0.0,
            },
            created_at=now + dt.timedelta(seconds=2),
        )
        db_session.add(msg_conv2)
        db_session.commit()

        tp_conv2 = Touchpoint(
            message_id=msg_conv2.id,
            message=msg_conv2,
            activity="CONV2_ACTIVITY",
            created_at=now + dt.timedelta(seconds=2),
        )
        db_session.add(tp_conv2)
        db_session.commit()

        # Create third conversation (branches from msg of conv2)
        conv3 = Conversation(
            id=uuid.uuid4(),
            meta={},
            created_at=now + dt.timedelta(seconds=3),
        )
        db_session.add(conv3)
        db_session.commit()

        msg_conv3 = Message(
            id=uuid.uuid4(),
            conversation_id=conv3.id,
            content="Conv3 message",
            type=MessageType.Human,
            parent_message_id=msg_conv2.id,  # Branch from msg of conv2
            timing_metadata={
                "simulated_timestamp": (now + dt.timedelta(seconds=3)).timestamp(),
                "pause_time": 0.0,
                "typing_time": 0.0,
                "thinking_time": 0.0,
            },
            created_at=now + dt.timedelta(seconds=3),
        )
        db_session.add(msg_conv3)
        db_session.commit()

        tp_conv3 = Touchpoint(
            message_id=msg_conv3.id,
            message=msg_conv3,
            activity="CONV3_ACTIVITY",
            created_at=now + dt.timedelta(seconds=3),
        )
        db_session.add(tp_conv3)
        db_session.commit()

        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        content = result.getvalue()
        lines = content.strip().split("\n")

        # Conv1: START + 2 msgs + END = 4 lines
        # Conv2: START + 2 parent msgs (chain from conv1) + 1 msg + END = 5 lines
        # Conv3: START + 2 parent msgs (chain from conv1) + 1 parent msg (from conv2) + 1 msg + END = 6 lines
        # Total: 1 (header) + 4 + 5 + 6 = 16 lines
        assert len(lines) == 16

        # Verify all activities are present
        assert "CONV1_ACTIVITY_0" in content
        assert "CONV1_ACTIVITY_1" in content
        assert "CONV2_ACTIVITY" in content
        assert "CONV3_ACTIVITY" in content

    def test_export_includes_start_marker(self, db_session, sample_conversation):
        """Test that export includes START marker for each conversation."""
        now = dt.datetime.now()
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=sample_conversation.id,
            content="Test message",
            type=MessageType.Human,
            timing_metadata={
                "simulated_timestamp": now.timestamp(),
                "pause_time": 0.0,
                "typing_time": 0.0,
                "thinking_time": 0.0,
            },
            created_at=now,
        )
        db_session.add(msg)
        db_session.commit()

        tp = Touchpoint(
            message_id=msg.id,
            message=msg,
            activity="TEST",
            created_at=now,
        )
        db_session.add(tp)
        db_session.commit()

        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        content = result.getvalue()
        assert "START-DIALOGUE-SYSTEM" in content

    def test_export_includes_end_marker(self, db_session, sample_conversation):
        """Test that export includes END marker for each conversation."""
        now = dt.datetime.now()
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=sample_conversation.id,
            content="Test message",
            type=MessageType.Human,
            timing_metadata={
                "simulated_timestamp": now.timestamp(),
                "pause_time": 0.0,
                "typing_time": 0.0,
                "thinking_time": 0.0,
            },
            created_at=now,
        )
        db_session.add(msg)
        db_session.commit()

        tp = Touchpoint(
            message_id=msg.id,
            message=msg,
            activity="TEST",
            created_at=now,
        )
        db_session.add(tp)
        db_session.commit()

        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        content = result.getvalue()
        assert "END - DIALOGUE - SYSTEM" in content

    def test_export_preserves_message_type(self, db_session, sample_conversation):
        """Test that message type is preserved in export."""
        now = dt.datetime.now()

        msg_human = Message(
            id=uuid.uuid4(),
            conversation_id=sample_conversation.id,
            content="Human message",
            type=MessageType.Human,
            timing_metadata={
                "simulated_timestamp": (now + dt.timedelta(seconds=1)).timestamp(),
                "pause_time": 0.0,
                "typing_time": 0.0,
                "thinking_time": 0.0,
            },
            created_at=now + dt.timedelta(seconds=1),
        )
        msg_ai = Message(
            id=uuid.uuid4(),
            conversation_id=sample_conversation.id,
            content="AI message",
            type=MessageType.AI,
            timing_metadata={
                "simulated_timestamp": (now + dt.timedelta(seconds=2)).timestamp(),
                "pause_time": 0.0,
                "typing_time": 0.0,
                "thinking_time": 0.0,
            },
            created_at=now + dt.timedelta(seconds=2),
        )

        db_session.add(msg_human)
        db_session.add(msg_ai)
        db_session.commit()

        tp_human = Touchpoint(
            message_id=msg_human.id,
            message=msg_human,
            activity="HUMAN_ACTIVITY",
            created_at=now + dt.timedelta(seconds=1),
        )
        tp_ai = Touchpoint(
            message_id=msg_ai.id,
            message=msg_ai,
            activity="AI_ACTIVITY",
            created_at=now + dt.timedelta(seconds=2),
        )

        db_session.add(tp_human)
        db_session.add(tp_ai)
        db_session.commit()

        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        content = result.getvalue()
        assert "human" in content
        assert "ai" in content

    def test_export_preserves_activity(self, db_session, sample_conversation):
        """Test that activity is preserved in export."""
        now = dt.datetime.now()
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=sample_conversation.id,
            content="Test message",
            type=MessageType.Human,
            timing_metadata={
                "simulated_timestamp": now.timestamp(),
                "pause_time": 0.0,
                "typing_time": 0.0,
                "thinking_time": 0.0,
            },
            created_at=now,
        )
        db_session.add(msg)
        db_session.commit()

        tp = Touchpoint(
            message_id=msg.id,
            message=msg,
            activity="SALDO_CONSULTA",
            created_at=now,
        )
        db_session.add(tp)
        db_session.commit()

        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        content = result.getvalue()
        assert "SALDO_CONSULTA" in content

    def test_export_timestamp_in_isoformat(self, db_session, sample_conversation):
        """Test that timestamps are exported in ISO format."""
        now = dt.datetime.now()
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=sample_conversation.id,
            content="Test message",
            type=MessageType.Human,
            timing_metadata={
                "simulated_timestamp": now.timestamp(),
                "pause_time": 0.0,
                "typing_time": 0.0,
                "thinking_time": 0.0,
            },
            created_at=now,
        )
        db_session.add(msg)
        db_session.commit()

        tp = Touchpoint(
            message_id=msg.id,
            message=msg,
            activity="TEST",
            created_at=now,
        )
        db_session.add(tp)
        db_session.commit()

        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        content = result.getvalue()
        lines = content.strip().split("\n")
        # Check that timestamps are in ISO format
        data_lines = [
            line for line in lines if "DIALOGUE" not in line and "event_id" not in line
        ]
        assert len(data_lines) > 0
        # Timestamp should contain 'T' for ISO format
        for line in data_lines:
            if line.strip():  # Skip empty lines
                assert "T" in line
