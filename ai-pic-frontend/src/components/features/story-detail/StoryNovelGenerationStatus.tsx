import { StatusPill } from "@/components/shared";
import type {
  StoryNovelContinuityLedger,
  StoryNovelRevision,
} from "@/utils/api/types";

export function storyNovelChapterProgress(revision: StoryNovelRevision) {
  const ledger = revision.continuity_ledger?.chapters || {};
  return (revision.generation_plan?.chapters || []).map((chapter) => {
    const checkpoint = ledger[String(chapter.position)] || {};
    return {
      position: chapter.position,
      title: chapter.title,
      bodyStatus: chapter.generation_status || checkpoint.status || "pending",
      extractionStatus:
        chapter.extraction_status || checkpoint.extraction_status || "pending",
      actualChars: chapter.actual_chars || checkpoint.char_count || 0,
      targetChars: chapter.target_chars,
    };
  });
}

export function storyNovelResumeLabel(
  ledger?: StoryNovelContinuityLedger | null,
): string {
  const recoveryPosition = ledger?.recovery_from_position;
  if (
    recoveryPosition &&
    ledger?.chapters?.[String(recoveryPosition)]?.status === "state_pending"
  ) {
    return "恢复状态提取（保留已保存正文）";
  }
  return ledger?.stale_from_position
    ? `从第 ${ledger.stale_from_position} 章续写至结尾`
    : "补齐缺失章节";
}

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
  const bodyCompleted = ledgerRows.filter((item) =>
    ["body_ready", "ready", "state_pending"].includes(item.status || ""),
  ).length;
  const statePending = ledgerRows.filter(
    (item) => item.status === "state_pending",
  ).length;
  const actualChars = ledgerRows.reduce(
    (total, item) => total + (item.char_count || 0),
    0,
  );
  const validated = ledgerRows.filter(
    (item) => item.state_validation?.status === "passed",
  ).length;
  const failedRows = ledgerRows.filter((item) => item.status === "gate_failed");
  const failures = failedRows.flatMap(
    (item) =>
      item.state_validation?.violations?.map(({ message }) => message) || [],
  );
  const chapterProgress = storyNovelChapterProgress(revision);
  return (
    <div>
      <div className="flex flex-wrap items-center gap-2">
        <StatusPill tone={plan?.status === "ready" ? "green" : "blue"}>
          规划 {plan?.status || "planning"}
        </StatusPill>
        <span className="text-xs text-gray-500">
          {actualChars || revision.total_words || 0}/
          {plan?.planned_target_chars || plan?.target_chars || "?"} 字符 · 正文{" "}
          {ledgerRows.length ? bodyCompleted : revision.chapters.length}/
          {plan?.chapter_count || "?"} · facts/记忆 {extracted}/
          {plan?.chapter_count || "?"}
          {plan?.schema === "story_novel_generation_plan.v2"
            ? ` · 状态门禁 ${validated}/${plan?.chapter_count || "?"}`
            : ""}
        </span>
        {statePending ? (
          <StatusPill tone="amber">
            {statePending} 章正文已保存，仅状态提取待恢复
          </StatusPill>
        ) : null}
        {failedRows.length ? (
          <StatusPill tone="red">{failedRows.length} 章门禁失败</StatusPill>
        ) : null}
      </div>
      {failures.length ? (
        <p className="mt-1 text-xs text-red-600">
          门禁失败：{failures.join("；")}
        </p>
      ) : null}
      {chapterProgress.length ? (
        <details className="mt-2 text-xs text-gray-600">
          <summary className="cursor-pointer">逐章正文与提取进度</summary>
          <div
            aria-label="逐章生成进度"
            className="mt-2 grid gap-1 md:grid-cols-2"
          >
            {chapterProgress.map((chapter) => (
              <div
                key={chapter.position}
                className="rounded border border-gray-200 px-2 py-1"
              >
                第 {chapter.position} 章 {chapter.title} · 正文{" "}
                {chapter.bodyStatus} · 提取 {chapter.extractionStatus} ·{" "}
                {chapter.actualChars}/{chapter.targetChars} 字符
              </div>
            ))}
          </div>
        </details>
      ) : null}
    </div>
  );
}
