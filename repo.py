"""Handles persistent data storage.
All functions can optionally be passed an aiosqlite connection object.
This keeps db ops atomic and allows for sharing of a connection across multiple ops.
"""

from __future__ import annotations

# import aiosqlite
from aiosqlite import connect, Connection
from .model import CrosspostRecord, Status


class CrosspostRepository:
    def __init__(self, path: str, conn: Connection | None = None):
        self.path = path
        if conn is None:
            conn = connect(self.path)

        # NOTE: Structure in the SQL database is NOT equal to whats described in model.py
        # Mainly that Crossposts cannot contain an instance of MessageRefs, so instead rows in MessageRefs refer to *Crossposts*.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS MessageRefs (
                id                  TEXT PRIMARY KEY,
                platform            TEXT,
                channel_id          INTEGER,
                message_id          INTEGER,
                guild_id            INTEGER,
                author_id           INTEGER,
                crossposted_from    TEXT FOREIGN KEY REFERENCES Crossposts(id),
            """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS Crossposts (
                id              TEXT PRIMARY KEY,
                status          TEXT NOT NULL,
                source          TEXT FOREIGN KEY REFERENCES MessageRefs(id),
                queue_message   TEXT FOREIGN KEY REFERENCES MessageRefs(id),
                reason          TEXT,
                created_at      INTEGER NOT NULL,
                decided_at      INTEGER,
            """)

    def save(self, record: CrosspostRecord, conn: Connection | None = None) -> None:
        """Save a crosspost record in its entirety to the db, new or existing."""
        # TODO: Implement
        raise NotImplementedError
        # Issue: Here I would need to do either of...
        # 1. Overwrite all columns for whatever row is getting updated, even if its just one or a few.
        # 2. Read *all* values for the given row and then overwrite the ones that get changed.
        # 3. Make a seperate `update` function that optionally patches the database instead of
        if conn is None:
            conn = connect(self.path)

        crosspost_dict = record.to_dict()
        # crossposts are not stored directly
        filtered_crosspost_dict = crosspost_dict.pop("crossposts")
        columns = filtered_crosspost_dict.keys()

        insert_statement = f"INSERT INTO Crossposts ({", ".join(columns)})"

        placeholders = ", ".join(["?" for column in columns])
        values_statement = f"VALUES ({placeholders})"

        set_statement = ", ".join([f"{k} = EXCLUDED.{k}" for column in columns])

        try:
            conn.execute(
                f"""
                {insert_statement}
                {values_statement}
                ON CONFLICT (id) DO UPDATE
                SET
            """,
                list(filtered_crosspost_dict),
            )
            for crosspost_message in crosspost_dict["crossposts"]:
            # TODO: Insert into MessageRefs where crossposted_from == Crossposts(id)

        except aiosqlite.Error as e:
            # TODO:
            pass

    def update(self, record_id: str, **kwds: str | int) -> None:
        """Update the database with kwargs."""
        raise NotImplementedError

    def get(self, record_id: str) -> CrosspostRecord | None:
        # TODO: Implement
        raise NotImplementedError

    def all(self, status: Status | None = None) -> list[CrosspostRecord]:
        # TODO: Implement
        raise NotImplementedError
