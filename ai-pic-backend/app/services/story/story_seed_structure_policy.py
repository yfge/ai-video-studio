"""Bounded hierarchy policy for large structured StorySeeds."""

STRUCTURE_ARC_SIZE = 32
MAX_STRUCTURE_TOKENS = 16000


def structure_ranges(expected_positions: list[int]) -> list[list[int]]:
    return [
        expected_positions[index : index + STRUCTURE_ARC_SIZE]
        for index in range(0, len(expected_positions), STRUCTURE_ARC_SIZE)
    ]


def progression_token_budget(expected_positions: list[int]) -> int:
    return min(
        MAX_STRUCTURE_TOKENS,
        max(6000, len(structure_ranges(expected_positions)) * 500),
    )


def chapter_batch_token_budget(positions: list[int]) -> int:
    return min(MAX_STRUCTURE_TOKENS, max(6000, len(positions) * 400))
