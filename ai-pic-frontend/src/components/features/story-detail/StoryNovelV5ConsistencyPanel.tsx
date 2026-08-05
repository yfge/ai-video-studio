import { OperatorPanel, StatusPill } from "@/components/shared";
import type { StoryNovelRevision } from "@/utils/api/types";

const shortHash = (value?: string | null) => value?.slice(0, 12) || "—";

export function StoryNovelV5ConsistencyPanel({
  revision,
}: {
  revision?: StoryNovelRevision | null;
}) {
  if (!revision) return null;
  const plan = revision.generation_plan;
  if (plan?.schema !== "story_novel_generation_plan.v5") return null;
  const counts = plan.canon_view?.counts;
  const ledger = revision.continuity_ledger?.chapters || {};
  const diagnostics = plan.schema_compile_diagnostics || [];
  return (
    <OperatorPanel>
      <div className="border-b border-gray-100 p-5">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="text-sm font-semibold">一致性模型</h3>
          <StatusPill
            tone={plan.schema_compile_status === "frozen" ? "green" : "amber"}
          >
            Schema {plan.schema_compile_status || "pending"}
          </StatusPill>
          <span className="text-xs text-gray-500">
            Schema {shortHash(plan.consistency_schema_hash)} · 初始快照{" "}
            {shortHash(plan.initial_snapshot_hash)} · 因果图{" "}
            {shortHash(plan.causal_graph_hash)}
          </span>
        </div>
        <p className="mt-2 text-xs text-gray-500">
          每个 Story 从冻结 StorySeed 自动编译；本页只读，修改 StorySeed 后需新建
          V5 Revision。
        </p>
      </div>
      <div className="grid gap-3 border-b border-gray-100 p-5 sm:grid-cols-5">
        {[
          ["实体类型", counts?.entity_types],
          ["谓词", counts?.predicates],
          ["事件类型", counts?.event_types],
          ["约束", counts?.constraints],
          ["视角", counts?.perspectives],
        ].map(([label, value]) => (
          <div key={String(label)} className="rounded border border-gray-200 p-3">
            <p className="text-xs text-gray-500">{label}</p>
            <p className="mt-1 text-lg font-semibold">{value ?? 0}</p>
          </div>
        ))}
      </div>
      {diagnostics.length ? (
        <div className="border-b border-gray-100 p-5 text-xs text-red-700">
          {diagnostics.map((item, index) => (
            <p key={`${item.code}-${index}`}>
              {item.code} · {item.message}
            </p>
          ))}
        </div>
      ) : null}
      <div className="p-5">
        <h4 className="text-xs font-semibold">逐章质量与状态链</h4>
        <div className="mt-3 grid gap-2 md:grid-cols-2">
          {(plan.chapters || []).map((chapter) => {
            const entry = ledger[String(chapter.position)] || {};
            return (
              <div
                key={chapter.position}
                className="rounded border border-gray-200 p-3 text-xs"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium">
                    第 {chapter.position} 章 · {chapter.title}
                  </span>
                  <StatusPill
                    tone={entry.status === "ready" ? "green" : "amber"}
                  >
                    {entry.status || "pending"}
                  </StatusPill>
                </div>
                <p className="mt-2 text-gray-500">
                  一致性 {entry.consistency_report?.status || "pending"} · 可读性{" "}
                  {entry.readability_report?.status || "pending"}
                  {entry.readability_report?.score != null
                    ? ` ${entry.readability_report.score}/10`
                    : ""}
                  {entry.repair_records?.length
                    ? ` · 返修 ${entry.repair_records.length}`
                    : ""}
                </p>
                <p className="mt-1 font-mono text-[11px] text-gray-400">
                  {shortHash(entry.snapshot_before_hash)} →{" "}
                  {shortHash(entry.snapshot_after_hash)}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </OperatorPanel>
  );
}
