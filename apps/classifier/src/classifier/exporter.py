import csv
from io import StringIO
from itertools import groupby

from sqlmodel import Session, col, select

from classifier.models import Touchpoint


class TouchpointExporter:
    def __init__(self, storage: Session) -> None:
        self.storage = storage

    def export_csv_str(self) -> StringIO:
        """Export Toucpoints into csv string.

        Each row has a event id, session id (as a case id), actor type (syste,
        AI, human), touchpoint and a timestamp. Each conversation/session/case
        has a START and END touchpoint marked as -1 and 9999, with the timestamp
        of the first and last message.
        """
        output = StringIO()

        writer = csv.writer(output)
        headers = "event_id,case_id,internal_id,actor,activity,timestamp"
        writer.writerow(headers)

        tps = self.storage.exec(
            select(Touchpoint).order_by(
                col(Touchpoint.session_id), col(Touchpoint.timestamp)
            )
        ).all()

        grouped_messages = {
            session_id: list(messages)
            for session_id, messages in groupby(tps, key=lambda x: x.session_id)
        }

        i = 0
        for session_id, messages in grouped_messages.items():
            # Start touchpoint
            writer.writerow(
                f"{i},{session_id},-1,System,START-DIALOGUE-SYSTEM,{messages[0].timestamp.isoformat()}"
            )
            i += 1

            for internal_id, msg in enumerate(messages):
                writer.writerow(
                    f"{i},{session_id},{internal_id},{msg.actor},{msg.activity},{msg.timestamp.isoformat()}"
                )
                i += 1

            # End touchpoint
            writer.writerow(
                f"{i},{session_id},99999,System,END-DIALOGUE-SYSTEM,{messages[-1].timestamp.isoformat()}"
            )
            i += 1
        return output
