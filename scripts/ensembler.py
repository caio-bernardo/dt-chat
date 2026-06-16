#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "typer",
# ]
# ///

import os
import shutil
import sqlite3
import uuid
from pathlib import Path
from typing import Annotated

import typer


def get_elected_activity(databases: list[sqlite3.Cursor], message_id: uuid.UUID) -> str:
    # Retrieve the corresponding activity from each database in databases
    activities = []
    for cursor in databases:
        activity = cursor.execute(
            "SELECT activity FROM touchpoint WHERE message_id = ?", (message_id,)
        ).fetchone()
        if activity:
            activities.append(activity[0])
        else:
            typer.echo(f"Error: could not find activity for {message_id} in {cursor}")
            activities.append("INVALID-TOUCHPOINT-SYSTEM")

    # Take the most common activity between all
    elected_activity = max(set(activities), key=activities.count)
    return elected_activity


def main(databases: Annotated[list[Path], typer.Argument()]) -> None:
    """Combines the databases activities into a single database, it copies the
    first database passed and for every touchpoint does an election between the
    provided databases."""
    in_cursors = []
    output = Path()
    try:
        assert len(databases) >= 2, ValueError(
            "Less than 2 databases, nothing to ensemble. Please provide at least 2 database files to combine."
        )
        # Copy the first database
        output = databases[0].with_name("output.db")
        shutil.copy(databases[0], output)

        # Optimization: create cursors for all databases
        in_cursors = [sqlite3.connect(db).cursor() for db in databases]

        with sqlite3.connect(output) as out_conn:
            out_cursor = out_conn.cursor()

            touchpoints = out_cursor.execute("SELECT * FROM touchpoint").fetchall()
            # For every touchpoint in the touchpoint table
            for touchpoint in touchpoints:
                # Get elected activity from ensemble
                message_id = touchpoint[1]
                elected_activity = get_elected_activity(in_cursors, message_id)

                # Update the the database with correct value
                out_cursor.execute(
                    "UPDATE touchpoint SET activity = ? WHERE message_id = ?",
                    (elected_activity, message_id),
                )
    except Exception as e:
        typer.echo(f"Error: {e}")
        if os.path.exists(output):
            os.remove(output)
    finally:
        for cursor in in_cursors:
            cursor.close()


if __name__ == "__main__":
    typer.run(main)
