from __future__ import annotations

from collections.abc import Sized
from typing import Any

'''
data extraction debugging utilities for agents, focused on compact gap reporting and fetch summaries.
'''


def log_data_fetch_debug(agent_id: str, ticker: str, **datasets: Any) -> None:
    """Print a compact snapshot of fetched inputs for an agent/ticker pair."""
    parts = []
    for name, value in datasets.items():
        if value is None:
            parts.append(f"{name}=missing")
        elif _is_sized_value(value):
            parts.append(f"{name}={len(value)}")
        else:
            parts.append(f"{name}=ok")

    print(f"[{agent_id}][{ticker}] fetched " + " ".join(parts))


def collect_data_gaps(*gaps: str | None) -> list[str]:
    """Filter optional gap messages into a compact list."""
    return [gap for gap in gaps if gap]


def gap_if_empty(name: str, value: Any, note: str | None = None) -> str | None:
    """Report a gap when a sized collection is empty."""
    if _is_sized_value(value) and len(value) == 0:
        return _format_gap(name, 0, note)
    return None


def gap_if_len_lt(name: str, value: Any, minimum: int, note: str | None = None) -> str | None:
    """Report a gap when a sized collection has fewer than `minimum` items."""
    if _is_sized_value(value) and len(value) < minimum:
        return _format_gap(name, len(value), note or f"<{minimum}")
    return None


def gap_if_none(name: str, value: Any, note: str | None = None) -> str | None:
    """Report a gap when a scalar value is missing."""
    if value is None:
        return _format_gap(name, "missing", note)
    return None


def gap_if_count_lt(name: str, count: int, minimum: int, note: str | None = None) -> str | None:
    """Report a gap when a derived count is below a threshold."""
    if count < minimum:
        return _format_gap(name, count, note or f"<{minimum}")
    return None


def _is_sized_value(value: Any) -> bool:
    return isinstance(value, Sized) and not isinstance(value, (str, bytes, bytearray))


def _format_gap(name: str, value: Any, note: str | None = None) -> str:
    return f"{name}={value}" if not note else f"{name}={value}({note})"
