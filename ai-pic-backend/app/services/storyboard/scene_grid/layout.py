"""Layout helpers for scene-level grid storyboard sheets."""

from __future__ import annotations

from dataclasses import dataclass

# Larger layouts than the Timeline grid; 12 (3x4) matches common practice for
# one-scene action sequences and stays within image-model text fidelity.
SUPPORTED_LAYOUTS: dict[int, tuple[int, int]] = {
    4: (2, 2),
    6: (2, 3),
    9: (3, 3),
    12: (3, 4),
    16: (4, 4),
}
DEFAULT_PANEL_COUNT = 12


@dataclass(frozen=True)
class SceneGridLayout:
    panel_count: int
    rows: int
    columns: int

    @property
    def label(self) -> str:
        return f"{self.rows}x{self.columns}"


def scene_grid_layout(panel_count: int | None) -> SceneGridLayout:
    """Return the smallest supported layout that fits panel_count."""
    requested = max(1, int(panel_count or DEFAULT_PANEL_COUNT))
    normalized = next(
        (count for count in sorted(SUPPORTED_LAYOUTS) if requested <= count),
        max(SUPPORTED_LAYOUTS),
    )
    rows, columns = SUPPORTED_LAYOUTS[normalized]
    return SceneGridLayout(panel_count=normalized, rows=rows, columns=columns)
