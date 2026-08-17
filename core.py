"""The handle and the coordinator.

``Crosspost`` is what a caller holds: it ties a persistent
``CrosspostRecord`` to the live platform layer, so you can do
``await crosspost.get_source()`` and get a real ``discord.Message``.

``Hub`` owns the config, persistence and the per-platform send/edit/delete
logic behind the approve / deny / purge transitions.
"""

from __future__ import annotations
from typing import Any, Callable
from model import CrosspostRecord, MessageRef, Platform, Status, _now


class Renderer:
    """Builds platform-native payloads for each `status` state of a record.

    Implementations return a dict of native kwargs for the platform
    I.E. for Discord: ``{"embed": ..., "view": ...}``
    """

    def approval_payload(self, record: CrosspostRecord) -> dict:
        raise NotImplementedError

    def crosspost_payload(self, record: CrosspostRecord, source: Any) -> dict:
        raise NotImplementedError

    def final_payload(self, record: CrosspostRecord) -> dict:
        raise NotImplementedError


class Crosspost:
    def __init__(self, record: CrosspostRecord, core: "Core"):
        self.record = record
        self.core = core

    # // Attributes (will be made persistant later)
    @property
    def id(self) -> str:
        return self.record.id

    @property
    def status(self) -> Status:
        return self.record.status

    @property
    def reason(self) -> str | None:
        return self.record.reason

    @property
    def crosspost_refs(self) -> list[MessageRef]:
        return list(self.record.crossposts)

    # // Live Objects //
    async def get_source(self) -> Any:
        """The OG message as a native object (e.g. ``discord.Message``)."""
        return await self.core.fetch_message(self.record.source)

    async def get_queue_message(self) -> Any | None:
        """The admin approval embed message as a native object."""
        if self.record.queue_message is None:
            return None
        return await self.core.fetch_message(self.record.queue_message)

    async def get_crossposts(self) -> -> list[Any]:
        """Posted crossposts as native objects, per platform, per respective feed channel."""
        return [await self.core.fetch_message(ref) for ref in self.record.crossposts]

    # // status changes //
    async def approve(self, reason: str | None = None) -> None:
        await self.core._approve(self, reason)

    async def deny(self, reason: str | None = None) -> None:
        await self.hub._deny(self, reason)

    async def purge(self, reason: str | None = None) -> None:
        await self.hub._purge(self, reason)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Crosspost {self.id} {self.status.value} source={self.record.source}>"


class Hub:
    def __init__(
        self,
        *,
        platforms: dict[Platform, Any],
    ):
