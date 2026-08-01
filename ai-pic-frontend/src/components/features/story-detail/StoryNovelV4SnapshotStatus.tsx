import type { StoryNovelRevision } from "@/utils/api/types";

export function StoryNovelV4SnapshotStatus({
  revision,
}: {
  revision: StoryNovelRevision;
}) {
  const plan = revision.generation_plan;
  if (plan?.schema !== "story_novel_generation_plan.v4") return null;
  const arc = plan.current_arc_plan;
  const entries = Object.values(revision.continuity_ledger?.chapters || {});
  const proposals = entries.flatMap((entry) =>
    (entry.chapter_intent?.entity_proposals || []).map((proposal) => ({
      ...proposal,
      lifecycle:
        entry.status === "ready"
          ? "已进入 Revision 世界"
          : ["gate_failed", "stale", "snapshot_stale"].includes(
              entry.status || "",
            )
          ? "已回滚"
          : "待审计",
    })),
  );
  const persistent = proposals.filter((item) => !item.transient);
  const committed = persistent.filter(
    (item) => item.lifecycle === "已进入 Revision 世界",
  );
  const plannedCharacters = arc?.instantiated_character_slots?.length || 0;
  const plannedScopes = arc?.instantiated_scope_slots?.length || 0;
  const liveScopes = plan.scope_graph?.nodes?.length || 0;
  const snapshots = entries.reduce(
    (total, entry) =>
      total + Object.keys(entry.model_call_snapshots || {}).length,
    0,
  );
  const latest = [...entries]
    .reverse()
    .find(
      (entry) => entry.planner_snapshot_hash || entry.arc_planner_snapshot_hash,
    );
  return (
    <div className="mt-2 rounded border border-blue-100 bg-blue-50 px-3 py-2 text-xs text-blue-900">
      <div>
        当前卷 {arc?.title || arc?.arc_id || "待冻结"}
        {arc ? ` · 第 ${arc.start_position}–${arc.end_position} 章` : ""}
        {plan.frozen_through_position
          ? ` · 合同冻结至第 ${plan.frozen_through_position} 章`
          : ""}
      </div>
      <div className="mt-1 text-blue-700">
        Planner snapshot{" "}
        {latest?.planner_snapshot_hash?.slice(0, 10) || "待生成"}
        {latest?.arc_planner_snapshot_hash
          ? ` · Arc ${latest.arc_planner_snapshot_hash.slice(0, 10)}`
          : ""}
        {` · 调用快照 ${snapshots} · 动态提案 ${proposals.length}（已落账 ${committed.length}）`}
      </div>
      <div className="mt-1 text-blue-700">
        本卷角色槽 {plannedCharacters} · 范围槽 {plannedScopes} · 初始范围{" "}
        {liveScopes}
      </div>
      {persistent.length ? (
        <div className="mt-1">
          新实体生命周期：
          {persistent
            .map(
              (item) =>
                `${item.name || item.proposal_handle}(${item.kind}，${
                  item.lifecycle
                })`,
            )
            .join("、")}
        </div>
      ) : null}
    </div>
  );
}
