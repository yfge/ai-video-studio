import { StatusPill } from "@/components/shared";
import type { StoryNovelRevision } from "@/utils/api/types";

export function StoryNovelGenerationStatus({
  revision,
}: {
  revision: StoryNovelRevision;
}) {
  const plan = revision.generation_plan;
  const ledgerRows = Object.values(revision.continuity_ledger?.chapters || {});
  const extracted = ledgerRows.filter(
    (item) => item.extraction_status === "ready",
  ).length;
  return (
    <div className="flex flex-wrap items-center gap-2">
      <StatusPill tone={plan?.status === "ready" ? "green" : "blue"}>
        规划 {plan?.status || "planning"}
      </StatusPill>
      <span className="text-xs text-gray-500">
        {revision.total_words || 0}/{plan?.target_chars || "?"} 字符 ·{" "}
        {revision.chapters.length}/{plan?.chapter_count || "?"} 章 · facts/记忆{" "}
        {extracted}/{plan?.chapter_count || "?"}
      </span>
    </div>
  );
}
