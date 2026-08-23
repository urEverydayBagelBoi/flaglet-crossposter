"""Handles persistent data storage.
All functions can optionally be passed an aiosqlite connection object.
This keeps db ops atomic and allows for sharing of a connection.
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

    def save(self, record: CrosspostRecord, conn: Connection | None = None):
        # TODO: Implement
        raise NotImplementedError

    def get(self, record_id: str) -> CrosspostRecord | None:
        # TODO: Implement
        raise NotImplementedError

    def all(self, status: Status | None = None) -> list[CrosspostRecord]:
        # TODO: Implement
        raise NotImplementedError
