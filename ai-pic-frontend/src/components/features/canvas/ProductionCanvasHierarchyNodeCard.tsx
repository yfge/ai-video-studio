import Link from "next/link";
import { operatorButtonClass } from "@/components/shared";
import type {
  HierarchyEntityType,
  PositionedHierarchyNode,
} from "./productionCanvasHierarchyModel";
import { hierarchyNodeActionHref } from "./productionCanvasHierarchyRoutes";

const entityMeta: Record<HierarchyEntityType, { label: string; tone: string }> =
  {
    ip: { label: "IP", tone: "border-sky-200 bg-sky-50 text-sky-700" },
    environment: {
      label: "环境",
      tone: "border-emerald-200 bg-emerald-50 text-emerald-700",
    },
    story: {
      label: "故事",
      tone: "border-violet-200 bg-violet-50 text-violet-700",
    },
    episode: {
      label: "剧集",
      tone: "border-amber-200 bg-amber-50 text-amber-700",
    },
    storyboard: {
      label: "分镜",
      tone: "border-blue-200 bg-blue-50 text-blue-700",
    },
    video: { label: "视频", tone: "border-rose-200 bg-rose-50 text-rose-700" },
  };

function statusLabel(status: string) {
  if (status === "ready" || status === "approved") return "已就绪";
  if (status === "generating" || status === "running") return "生成中";
  if (status === "missing" || status === "blocked") return "待生成";
  if (status === "empty") return "暂无数据";
  return status || "可查看";
}

export function ProductionCanvasHierarchyNodeCard({
  error,
  expanded,
  loading,
  node,
  selected,
  onSelect,
  onToggle,
}: {
  error?: string | null;
  expanded: boolean;
  loading: boolean;
  node: PositionedHierarchyNode;
  selected: boolean;
  onSelect: (nodeId: string) => void;
  onToggle: (nodeId: string) => void;
}) {
  const meta = entityMeta[node.entityType];
  const typeLabel = node.displayTypeLabel || meta.label;
  const actionHref = hierarchyNodeActionHref(node);
  return (
    <article
      aria-current={selected ? "true" : undefined}
      className={`absolute rounded-xl border bg-white shadow-sm transition ${
        selected
          ? "border-blue-400 ring-2 ring-blue-200"
          : "border-slate-200 hover:shadow-md"
      } ${node.empty ? "border-dashed bg-slate-50" : ""}`}
      data-hierarchy-entity-type={node.entityType}
      data-hierarchy-node={node.id}
      style={{
        height: node.height,
        left: node.x,
        top: node.y,
        width: node.width,
      }}
    >
      <button
        aria-label={`${typeLabel} ${node.title}`}
        aria-pressed={selected}
        className="block h-full w-full rounded-xl p-3 pb-10 text-left"
        type="button"
        onClick={() => onSelect(node.id)}
      >
        <div className="flex items-center justify-between gap-2">
          <span
            className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold ${meta.tone}`}
          >
            {typeLabel}
          </span>
          <span className="truncate text-[10px] text-slate-500">
            {node.empty && node.status !== "generating"
              ? "暂无数据"
              : statusLabel(node.status)}
          </span>
        </div>
        <h3 className="mt-2 line-clamp-1 text-xs font-semibold text-slate-950">
          {node.title}
        </h3>
        {node.detail ? (
          <p className="mt-1 line-clamp-2 text-[11px] leading-4 text-slate-500">
            {node.detail}
          </p>
        ) : null}
      </button>
      <div className="absolute bottom-2 left-3 right-3 flex items-center gap-2">
        {node.expandable && !node.empty ? (
          <button
            aria-busy={loading || undefined}
            aria-expanded={expanded}
            className={operatorButtonClass(
              "ghost",
              "h-6 min-w-0 flex-1 justify-start px-1 text-[10px]",
            )}
            disabled={loading}
            type="button"
            onClick={() => onToggle(node.id)}
          >
            {loading
              ? "加载中"
              : expanded
              ? "收起"
              : node.hiddenDescendantCount
              ? `展开 · 已加载 ${node.hiddenDescendantCount} 项`
              : "展开"}
          </button>
        ) : (
          <span className="min-w-0 flex-1 truncate text-[10px] text-slate-400">
            {error || (node.empty ? "该层暂无实体" : "稳定业务实体")}
          </span>
        )}
        {actionHref && !node.empty ? (
          <Link
            aria-label={`打开${typeLabel} ${node.title}`}
            className={operatorButtonClass("secondary", "h-6 px-2 text-[10px]")}
            href={actionHref}
          >
            打开
          </Link>
        ) : null}
      </div>
      {error && node.expandable ? (
        <div
          className="absolute left-3 right-3 top-[calc(100%+4px)] z-20 rounded bg-red-50 px-2 py-1 text-[10px] text-red-700 shadow"
          role="alert"
        >
          {error}
        </div>
      ) : null}
    </article>
  );
}
