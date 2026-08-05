import type {
  StorySeedStructuredChapter,
  StorySeedStructuredOutline,
} from "@/utils/api/types";

export function progressionCovers(
  outline: StorySeedStructuredOutline,
  chapters: StorySeedStructuredChapter[],
) {
  if (outline.planning_structure_version !== 1) return false;
  const positions = (outline.progression_arcs ?? []).flatMap((arc) =>
    Array.from(
      { length: arc.end_position - arc.start_position + 1 },
      (_, index) => arc.start_position + index,
    ),
  );
  return (
    positions.length === chapters.length &&
    positions.every((position, index) => position === index + 1)
  );
}

export function visibleProgressionChapters(
  outline: StorySeedStructuredOutline,
  selectedArcId: string,
) {
  const arcs = outline.progression_arcs ?? [];
  const selectedArc =
    arcs.find((arc) => arc.arc_id === selectedArcId) ?? arcs[0];
  const chapterRows = outline.chapters
    .map((chapter, index) => ({ chapter, index }))
    .filter(
      ({ chapter }) =>
        !selectedArc ||
        (chapter.position >= selectedArc.start_position &&
          chapter.position <= selectedArc.end_position),
    );
  return { arcs, selectedArc, chapterRows };
}
