import csv
import uuid

from bancobot.models import Conversation, MessageType
from classifier.models import Touchpoint
from exporter.cli import cli_main as exporter_main
from sqlmodel import Session, SQLModel, create_engine


def test_cli_writes_csv_file(tmp_path, make_message):
    db_file = tmp_path / "touchpoints.db"
    out_file = tmp_path / "out.csv"

    db_url = f"sqlite:///{db_file}"

    engine = create_engine(db_url)
    SQLModel.metadata.create_all(engine)

    # Create a minimal dataset: 1 conversation, 1 message, 1 touchpoint
    conversation_id = uuid.UUID("00000000-0000-0000-0000-000000000111")
    message_id = uuid.UUID("00000000-0000-0000-0000-000000000222")

    conversation = Conversation(
        id=conversation_id,
        meta={"bot_label": "cli-bot"},
    )
    message = make_message(
        conversation_id=conversation_id,
        message_id=message_id,
        content="hello",
        msg_type=MessageType.Human,
        seconds_offset=5,
    )
    tp = Touchpoint(message_id=message_id, activity="HELLO_TP")

    with Session(engine) as session:
        session.add(conversation)
        session.add(message)
        session.add(tp)
        session.commit()

    exporter_main(file_output=str(out_file), db_path=db_url)

    assert out_file.exists()
    text = out_file.read_text(encoding="utf-8")

    reader = csv.DictReader(text.splitlines())
    rows = list(reader)

    # START + touchpoint + END
    assert len(rows) == 3
    assert rows[0]["activity"] == "START-DIALOGUE-SYSTEM"
    assert rows[1]["activity"] == "HELLO_TP"
    assert rows[2]["activity"] == "END-DIALOGUE-SYSTEM"

    # It should write the expanded exporter schema.
    assert "bot_label" in (reader.fieldnames or [])
    assert rows[1]["bot_label"] == "cli-bot"
