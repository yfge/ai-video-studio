"""Storyboard grid layout helpers."""

from __future__ import annotations

from dataclasses import dataclass

SUPPORTED_PANEL_COUNTS = (2, 4, 6, 9)


@dataclass(frozen=True)
class GridLayout:
    panel_count: int
    columns: int
    rows: int

    @property
    def label(self) -> str:
        return f"{self.columns}x{self.rows}"


def grid_layout(panel_count: int) -> GridLayout:
    """Return the smallest supported storyboard grid layout for a clip count."""

    requested_count = max(1, panel_count)
    normalized_count = next(
        (count for count in SUPPORTED_PANEL_COUNTS if requested_count <= count),
        SUPPORTED_PANEL_COUNTS[-1],
    )

    if normalized_count == 2:
        return GridLayout(panel_count=2, columns=2, rows=1)
    if normalized_count == 4:
        return GridLayout(panel_count=4, columns=2, rows=2)
    if normalized_count == 6:
        return GridLayout(panel_count=6, columns=3, rows=2)
    return GridLayout(panel_count=9, columns=3, rows=3)
