import Link from "next/link";
import { operatorButtonClass } from "@/components/shared";
import type { HierarchyNode } from "./productionCanvasHierarchyModel";
import { hierarchyNodeActionHref } from "./productionCanvasHierarchyRoutes";

export function ProductionCanvasHierarchyInspector({
  node,
}: {
  node?: HierarchyNode;
}) {
  if (!node) {
    return (
      <p className="text-xs leading-5 text-slate-500">
        选择实体查看稳定标识与入口。
      </p>
    );
  }
  const actionHref = hierarchyNodeActionHref(node);
  return (
    <div className="space-y-3 text-xs text-slate-600">
      <div>
        <div className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">
          {node.entityType}
        </div>
        <div className="mt-1 font-semibold text-slate-950">{node.title}</div>
        {node.detail ? <p className="mt-1 leading-5">{node.detail}</p> : null}
      </div>
      <dl className="grid grid-cols-[78px_minmax(0,1fr)] gap-x-2 gap-y-1 text-[11px]">
        <dt className="text-slate-400">实体 ID</dt>
        <dd className="truncate font-mono">{String(node.entityId)}</dd>
        {node.businessId ? (
          <>
            <dt className="text-slate-400">业务 ID</dt>
            <dd className="truncate font-mono">{node.businessId}</dd>
          </>
        ) : null}
        {node.clipId ? (
          <>
            <dt className="text-slate-400">stable clip</dt>
            <dd className="break-all font-mono">{node.clipId}</dd>
          </>
        ) : null}
        {node.timelineId ? (
          <>
            <dt className="text-slate-400">Timeline</dt>
            <dd>{`${node.timelineId} · v${node.timelineVersion || "?"}`}</dd>
          </>
        ) : null}
        {node.assetLinkId ? (
          <>
            <dt className="text-slate-400">资产绑定</dt>
            <dd>{node.assetLinkId}</dd>
          </>
        ) : null}
      </dl>
      {actionHref && !node.empty ? (
        <Link
          className={operatorButtonClass("secondary", "w-full")}
          href={actionHref}
        >
          打开实体工作区
        </Link>
      ) : null}
      {node.videoUrl ? (
        <a
          className={operatorButtonClass("primary", "w-full")}
          href={node.videoUrl}
          rel="noreferrer"
          target="_blank"
        >
          播放当前视频
        </a>
      ) : null}
    </div>
  );
}
