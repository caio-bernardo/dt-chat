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

ties = 0


def get_elected_activity(databases: list[sqlite3.Cursor], message_id: uuid.UUID) -> str:
    # Retrieve the corresponding activity from each database in databases
    activities = []
    for cursor in databases:
        activity = cursor.execute(
            "SELECT activity FROM touchpoint WHERE message_id = ?", (message_id,)
        ).fetchone()
        # desconsider invalid touchpoints
        if activity and activity[0] == "INVALID-TOUCHPOINT-SYSTEM":
            pass
        # add activity
        elif activity:
            activities.append(activity[0])
        # if no activity print error
        else:
            typer.echo(f"Error: could not find activity for {message_id} in {cursor}")

    if len(activities) == 0:
        return "INVALID-TOUCHPOINT-SYSTEM"

    # Count occurrences of each activity
    activity_counts = {
        activity: activities.count(activity) for activity in set(activities)
    }
    max_count = max(activity_counts.values())

    # Find all activities that share the highest count (i.e., ties)
    top_activities = [a for a, count in activity_counts.items() if count == max_count]

    # If there is a tie, use the first database's activity as the tiebreaker
    if len(top_activities) > 1:
        global ties
        ties += 1
        typer.echo(f"Tie detected for message_id {message_id}: {top_activities}")
        # Use the first database's activity to break the tie
        for cursor in databases:
            first_db_activity = cursor.execute(
                "SELECT activity FROM touchpoint WHERE message_id = ?", (message_id,)
            ).fetchone()
            if first_db_activity and first_db_activity[0] in top_activities:
                elected_activity = first_db_activity[0]
                break
        else:
            # Fallback: pick the lexicographically first activity among the tied ones
            elected_activity = sorted(top_activities)[0]
    else:
        elected_activity = top_activities[0]

    # Take the most common activity between all
    return elected_activity


def main(
    databases: Annotated[list[Path], typer.Argument()],
    output_name: Annotated[str, typer.Option()] = "output.db",
) -> None:
    """Combines the databases activities into a single database, it copies the
    first database passed and for every touchpoint does an election between the
    provided databases. In case of ties the first database is used to decide it"""
    in_cursors = []
    output = Path()
    try:
        assert len(databases) >= 2, ValueError(
            "Less than 2 databases, nothing to ensemble. Please provide at least 2 database files to combine."
        )
        # Copy the first database
        output = databases[0].with_name(output_name)
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

        typer.echo(f"Ensembled {len(touchpoints)} touchpoints")
        typer.echo(f"Output: {output}")
        global ties
        typer.echo(f"Number of Ties: {ties}")
    except Exception as e:
        typer.echo(f"Error: {e}")
        if os.path.exists(output):
            os.remove(output)
    finally:
        for cursor in in_cursors:
            cursor.close()


if __name__ == "__main__":
    typer.run(main)
