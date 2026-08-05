import { StatusPill } from "@/components/shared";
import type {
  StoryNovelChapterLedger,
  StoryNovelContinuityLedger,
  StoryNovelGenerationStage,
  StoryNovelRevision,
} from "@/utils/api/types";
import { StoryNovelV4SnapshotStatus } from "./StoryNovelV4SnapshotStatus";

const LEGACY_STAGE_MAP: Record<string, StoryNovelGenerationStage> = {
  planning: "chapter_planning",
  body_ready: "audit",
  state_pending: "audit",
  extraction_ready: "memory_ready",
  ready: "ready",
};

function chapterStage(
  checkpoint: StoryNovelChapterLedger,
  generationStatus?: string | null,
): StoryNovelGenerationStage | string {
  if (checkpoint.stage) return checkpoint.stage;
  const fallback =
    generationStatus ||
    checkpoint.generation_status ||
    checkpoint.status ||
    "pending";
  return LEGACY_STAGE_MAP[fallback] || fallback;
}

function chapterUsage(checkpoint: StoryNovelChapterLedger) {
  return Object.values(checkpoint.stage_metrics || {}).reduce<{
    calls: number;
    tokens: number;
    latencyMs: number;
  }>(
    (total, metric) => ({
      calls: total.calls + (metric?.calls || 0),
      tokens:
        total.tokens +
        (metric?.input_tokens || 0) +
        (metric?.output_tokens || 0),
      latencyMs: total.latencyMs + (metric?.latency_ms || 0),
    }),
    { calls: 0, tokens: 0, latencyMs: 0 },
  );
}

function formatLatency(latencyMs: number) {
  return latencyMs >= 1000
    ? `${(latencyMs / 1000).toFixed(1)}s`
    : `${latencyMs}ms`;
}

export function storyNovelChapterProgress(revision: StoryNovelRevision) {
  const ledger = revision.continuity_ledger?.chapters || {};
  return (revision.generation_plan?.chapters || []).map((chapter) => {
    const checkpoint: StoryNovelChapterLedger =
      ledger[String(chapter.position)] || {};
    return {
      position: chapter.position,
      title: chapter.title,
      bodyStatus: chapter.generation_status || checkpoint.status || "pending",
      extractionStatus:
        chapter.extraction_status || checkpoint.extraction_status || "pending",
      actualChars: chapter.actual_chars || checkpoint.char_count || 0,
      targetChars: chapter.target_chars,
      stage: chapterStage(checkpoint, chapter.generation_status),
      usage: chapterUsage(checkpoint),
      failedBlocks: checkpoint.failed_block_ids || [],
      consistencyStatus: checkpoint.consistency_report?.status || "pending",
      readabilityStatus: checkpoint.readability_report?.status || "pending",
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
    [
      "body_ready",
      "audit",
      "auditing",
      "memory_ready",
      "ready",
      "review_required",
      "state_pending",
    ].includes(item.status || ""),
  ).length;
  const statePending = ledgerRows.filter(
    (item) => item.status === "state_pending",
  ).length;
  const actualChars = ledgerRows.reduce(
    (total, item) => total + (item.char_count || 0),
    0,
  );
  const validated = ledgerRows.filter(
    (item) =>
      item.state_validation?.status === "passed" ||
      item.consistency_report?.status === "passed",
  ).length;
  const usage = ledgerRows.reduce(
    (total, item) => {
      const chapter = chapterUsage(item);
      return {
        calls: total.calls + chapter.calls,
        tokens: total.tokens + chapter.tokens,
        latencyMs: total.latencyMs + chapter.latencyMs,
      };
    },
    { calls: 0, tokens: 0, latencyMs: 0 },
  );
  const failedRows = ledgerRows.filter((item) =>
    ["gate_failed", "review_required"].includes(item.status || ""),
  );
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
          {plan?.schema?.startsWith("story_novel_generation_plan.v")
            ? ` · 状态门禁 ${validated}/${plan?.chapter_count || "?"}`
            : ""}
        </span>
        {usage.calls || usage.tokens || usage.latencyMs ? (
          <span className="text-xs text-gray-500">
            模型调用 {usage.calls} · Tokens {usage.tokens.toLocaleString()} ·
            延迟 {formatLatency(usage.latencyMs)}
          </span>
        ) : null}
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
                {chapter.actualChars}/{chapter.targetChars} 字符 · 阶段{" "}
                {chapter.stage}
                {plan?.schema === "story_novel_generation_plan.v5"
                  ? ` · 一致性 ${chapter.consistencyStatus} · 可读性 ${chapter.readabilityStatus}`
                  : ""}
                {chapter.usage.calls ||
                chapter.usage.tokens ||
                chapter.usage.latencyMs
                  ? ` · 调用 ${
                      chapter.usage.calls
                    } · Tokens ${chapter.usage.tokens.toLocaleString()} · 延迟 ${formatLatency(
                      chapter.usage.latencyMs,
                    )}`
                  : ""}
                {chapter.failedBlocks.length
                  ? ` · 失败 blocks ${chapter.failedBlocks.join(", ")}`
                  : ""}
              </div>
            ))}
          </div>
        </details>
      ) : null}
      <StoryNovelV4SnapshotStatus revision={revision} />
    </div>
  );
}
