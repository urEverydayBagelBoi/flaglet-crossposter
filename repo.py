"""Handles persistent data storage.
All functions can optionally be passed an aiosqlite connection object.
This keeps db ops atomic and allows for sharing of a connection across multiple ops.
"""

from __future__ import annotations

# from aiosqlite import connect, Connection
import aiosqlite
import sqlite3
from .model import CrosspostRecord, Status
from dataclasses import dataclass

from datetime import timezone


class CrosspostRepository:

    crossposts_columns = [
        "id",
        "message_id",
        "author_id",
        "channel_id",
        "guild_id",
        "platform",
        "crossposted_from",
    ]

    messagerefs_columns = [
        "id",
        "message_id",
        "author_id",
        "channel_id",
        "guild_id",
        "platform",
        "crossposted_from",
        "added_as",
    ]

    def __init__(self, path: str):
        self.path = path
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        # NOTE: Structure in the SQL database is NOT equal to whats described in model.py
        # Mainly that Crossposts cannot contain an instance of MessageRefs, so instead rows in MessageRefs refer to *Crossposts* from which they originate.
        # MessageRefs also get added_as for debugging purposes

        # conn.execute("PRAGMA foreign_keys = ON")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS MessageRefs (
            id                  TEXT PRIMARY KEY,
            message_id          INTEGER,
            author_id           INTEGER,
            channel_id          INTEGER,
            guild_id            INTEGER,
            platform            TEXT,
            crossposted_from    TEXT,
            added_as            TEXT,
            FOREIGN KEY(crossposted_from) REFERENCES Crossposts(id)
        )
        """)
        # FOREIGN KEY(crossposted_from) REFERENCES Crossposts(id),

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Crossposts (
            id              TEXT PRIMARY KEY,
            status          TEXT NOT NULL,
            source          TEXT,
            queue_message   TEXT,
            reason          TEXT,
            created_at      INTEGER NOT NULL,
            decided_at      INTEGER,
            FOREIGN KEY(queue_message) REFERENCES MessageRefs(id),
            FOREIGN KEY(source) REFERENCES MessageRefs(id)
        )
        """)
        conn.commit()
        conn.close()

    async def save(
        self, record: CrosspostRecord, conn: Connection | None = None
    ) -> None:
        """Save a crosspost record in its entirety to the db, new or existing."""
        if conn is None:
            conn = aiosqlite.connect(self.path)

        # // Insert into Crossposts //
        _ = ", ".join(["?" for _ in range(1, len(self.crossposts_columns))])
        question_marks = f"({_})"

        # NOTE: Should be in order as added to database
        values = (
            record.id,
            record.status.value,
            record.source.message_id,
            record.queue_message.message_id if record.queue_message else None,
            record.reason,
            int(record.created_at.astimezone(timezone.utc).timestamp()),
            (
                int(record.decided_at.astimezone(timezone.utc).timestamp())
                if record.decided_at
                else None
            ),
        )

        set_statement = ""
        update_columns = self.crossposts_columns.pop("id")
        for i, column in enumerate(update_columns):
            if i == len(update_columns) - 1:
                set_statement += f"{column} = EXCLUDED.{column}"
            set_statement += f"{column} = EXCLUDED.{column},\n"

        # This inserts into the database for every column.
        # If the ID already exists (the record exists), overwrite all values with the record.
        conn.execute(
            f"""
            INSERT INTO Crossposts
            VALUES {question_marks}
            ON CONFLICT(id) DO UPDATE SET
            {set_statement}
            """,
            values,
        )

        # // Insert crossposted messages (if any) into MessageRefs with crossposted_from set //
        _ = ", ".join(["?" for _ in self.messagerefs_columns])
        question_marks = f"({_})"

        value_sets = []
        for message in record.crossposts:
            values = list(message.to_dict().values()).extend(
                [record.id, "crosspost"]  # crossposted_from  # added_as
            )
            value_sets.append(values)

        # If a given message already exists, just skip it with no update.
        # They are fundamentally immutable and cannot overlap.
        # I.E. a message can't change id, message_id, author, channel, guild or platform.
        conn.executemany(
            f"""
            INSERT INTO MessageRefs VALUES {question_marks}
            ON CONFLICT DO NOTHING
            """,
            value_sets,
        )

    def update(self, record_id: str, **kwds: str | int) -> None:
        """Update the database with kwargs."""
        raise NotImplementedError

    def get(self, record_id: str) -> CrosspostRecord | None:
        # TODO: Implement
        raise NotImplementedError

    def all(self, status: Status | None = None) -> list[CrosspostRecord]:
        # TODO: Implement
        raise NotImplementedError
