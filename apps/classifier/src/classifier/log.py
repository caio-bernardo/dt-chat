from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

LOG_FILE: str = "classifier-log.csv"


def add_log_entry(
    actor: str,
    msg: str,
    model_name: str,
    data: Dict[str, Any],
    file_path: str | Path = LOG_FILE,
) -> None:
    complete_file_path = f"{model_name.replace('/', '-')}-{file_path}"
    """Append a log entry to a CSV file containing a list of entries."""
    path = Path(complete_file_path)
    is_new_file = not path.exists() or path.stat().st_size == 0

    # Escape line breaks so each log entry stays on a single CSV line.
    msg_escaped = msg.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")

    with open(path, "a", encoding="utf-8") as f:
        if is_new_file:
            f.write("actor;msg;timestamp;model,data\n")
        f.write(
            f"{actor};{msg_escaped};{datetime.now().isoformat()};{model_name};{json.dumps(data, ensure_ascii=False)}\n",
        )
