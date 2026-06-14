"""Context ingestion interface + merge/dedup base (T019, FR-002).

The full set of free-tier providers (sentiment, news, macro, security, systemic) lands with US2.
Here we define the common ``ContextProvider`` interface and the security-incident merge/dedup
helper (a pattern inherited from the sibling project): the same incident reported by several feeds
must be deduplicated by contract + source.
"""

from __future__ import annotations

from typing import Any, Protocol


class ContextProvider(Protocol):
    """A single context feed (Fear&Greed, GDELT, PeckShield, ...)."""

    async def fetch(self) -> dict[str, Any]: ...


def merge_security_flags(flag_lists: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Deduplicate security flags by (asset, source) across providers."""
    seen: set[tuple[Any, Any]] = set()
    merged: list[dict[str, Any]] = []
    for flags in flag_lists:
        for flag in flags:
            key = (flag.get("asset"), flag.get("source"))
            if key in seen:
                continue
            seen.add(key)
            merged.append(flag)
    return merged
