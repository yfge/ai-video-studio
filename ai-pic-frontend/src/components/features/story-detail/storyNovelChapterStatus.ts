import type {
  NovelChapterLength,
  StoryNovelChapter,
  StoryNovelRevision,
} from "@/utils/api/types";

export function resolveNovelChapterStatus(
  revision: StoryNovelRevision,
  chapter: StoryNovelChapter,
) {
  const ledger =
    revision.continuity_ledger?.chapters?.[chapter.business_id] ||
    revision.continuity_ledger?.chapters?.[String(chapter.position)];
  const planned = revision.generation_plan?.chapters.find(
    (item) => item.position === chapter.position,
  );
  const length: NovelChapterLength | undefined =
    planned?.length ||
    (planned?.min_chars && planned.max_chars
      ? {
          min_chars: planned.min_chars,
          target_chars: planned.target_chars,
          max_chars: planned.max_chars,
          source: "profile_default",
        }
      : undefined);
  return {
    actualChars:
      chapter.actual_chars ??
      planned?.actual_chars ??
      ledger?.char_count ??
      chapter.content_text.replace(/\s/g, "").length,
    generationStatus:
      chapter.generation_status ||
      planned?.generation_status ||
      ledger?.generation_status ||
      ledger?.status ||
      (chapter.content_text ? "body_ready" : "pending"),
    extractionStatus:
      chapter.extraction_status ||
      planned?.extraction_status ||
      ledger?.extraction_status ||
      "pending",
    length,
  };
}
