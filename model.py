from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
import uuid

# from datetime import datetime, timezone
import datetime


class Platform(str, Enum):
    """A platform to be crossposted to or from."""

    DISCORD = "discord"
    STOAT = "stoat"


class Status(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    PURGED = "purged"


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


@dataclass
class MessageRef:
    """Pointer to a message on any platform
    Discord: ``(guild_id, channel_id, message.id)``.
    """

    platform: Platform
    # Note to self; may want to make these `int | str` if platforms get added with hex IDs
    channel_id: int
    message_id: int
    guild_id: int
    author_id: int
    id: str = field(
        default_factory=lambda: uuid.uuid4().hex
    )  # used only for db at the moment
    # NOTE: I might change this later idk if this is a good way of doing this

    def to_dict(self) -> dict:
        return {
            "platform": self.platform.value,
            "channel_id": self.channel_id,
            "message_id": self.message_id,
            "guild_id": self.guild_id,
            "author_id": self.author_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> MessageRef:
        return cls(
            platform=Platform(data["platform"]),
            channel_id=data["channel_id"],
            message_id=data["message_id"],
            guild_id=data.get("guild_id"),
            author_id=data.get("author_id"),
        )

    def __str__(self) -> str:
        if self.platform is Platform.DISCORD:
            return (
                f"https://discord.com/channels/{self.guild_id}"
                f"/{self.channel_id}/{self.message_id}"
            )
        return f"<{self.platform.value}://{self.channel_id}/{self.message_id}>"


@dataclass
class CrosspostRecord:
    """Represents a crosspost in memory.
    No database code here.
    """

    source: MessageRef
    status: Status = Status.PENDING
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    queue_message: MessageRef | None = None
    crossposts: list[MessageRef] = field(default_factory=list)
    reason: str | None = None
    created_at: datetime.datetime = field(default_factory=_now)
    decided_at: datetime.datetime | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status.value,
            "source": self.source.to_dict(),
            "queue_message": (
                self.queue_message.to_dict() if self.queue_message else None
            ),
            "crossposts": [m.to_dict() for m in self.crossposts],
            "reason": self.reason,
            "created_at": self.created_at,
            "decided_at": self.decided_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CrosspostRecord":
        return cls(
            id=data["id"],
            status=Status(data["status"]),
            source=MessageRef.from_dict(data["source"]),
            queue_message=(
                MessageRef.from_dict(data["queue_message"])
                if data.get("queue_message")
                else None
            ),
            crossposts=[MessageRef.from_dict(m) for m in data.get("crossposts", [])],
            reason=data.get("reason"),
            created_at=data.get("created_at", _now()),
            decided_at=data.get("decided_at"),
        )
