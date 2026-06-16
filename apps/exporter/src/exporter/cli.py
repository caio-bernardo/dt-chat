from sqlmodel import Session, create_engine

from .service import TouchpointExporter


def cli_main(file_output: str = "output.csv", db_path: str = "db/touchpoints.db"):
    """Export touchpoints to a csv file, retrieve touchpoints from `db_path`.

    The file is composable of an global event id, a case id (represents the
    conversation session), the producer/actor of the message, the touchpoint
    type, a timestamp of the message and a internal id, representing the age of the message in the conversatio.

    Each conversation has a `START` and `END` touchpoint with internal ids -1
    and 99999 respectively, they contain the timestamp of the first and last
    message in the conversation.
    """
    engine = create_engine("sqlite:///" + db_path)

    with Session(engine) as session:
        exporter = TouchpointExporter(storage=session)

        print("Exporting touchpoints")
        with open(file_output, "w+") as f:
            contents = exporter.export_csv_str()
            f.write(contents.getvalue())

        print("Exporting Complete.")
