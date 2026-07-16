import { operatorButtonClass } from "@/components/shared";
import type {
  ProductionCanvasMediaCandidate,
  ProductionCanvasStaleImpactNode,
} from "@/utils/api/types";
import { ProductionCanvasCandidateItem } from "./ProductionCanvasCandidateItem";
import { canDirectlyPlaceProductionCanvasVideo } from "./productionCanvasCandidateCapabilities";
import type { ProductionCanvasNode } from "./productionCanvasModel";

export type ProductionCanvasCandidateBusyId = number | "load" | "place" | null;

export function ProductionCanvasCandidateReviewPanel({
  busyId,
  canApprove,
  canBranch,
  candidates,
  error,
  node,
  notice,
  onApprove,
  onBranch,
  onPlaceInTimeline,
  onRefresh,
  onReject,
  selectedOutputId,
  staleImpact,
}: {
  busyId: ProductionCanvasCandidateBusyId;
  canApprove: boolean;
  canBranch: boolean;
  candidates: ProductionCanvasMediaCandidate[];
  error: string | null;
  node: ProductionCanvasNode;
  notice: string | null;
  onApprove: (candidate: ProductionCanvasMediaCandidate) => void;
  onBranch: (
    candidate: ProductionCanvasMediaCandidate,
    instruction: string,
  ) => void;
  onPlaceInTimeline: () => void;
  onRefresh: () => void;
  onReject: (candidate: ProductionCanvasMediaCandidate, reason: string) => void;
  selectedOutputId: number | null;
  staleImpact: ProductionCanvasStaleImpactNode[];
}) {
  return (
    <section
      className="border-t border-gray-100 pt-3"
      aria-label="媒体候选评审"
    >
      <div className="flex items-center justify-between gap-2">
        <div className="text-xs font-semibold text-gray-700">候选评审</div>
        <button
          type="button"
          className={operatorButtonClass("secondary", "h-7 px-2 text-[11px]")}
          disabled={busyId !== null}
          onClick={onRefresh}
        >
          {busyId === "load" ? "加载中" : "刷新"}
        </button>
      </div>
      {candidates.length ? (
        <div className="mt-2 divide-y divide-gray-100 border-y border-gray-100">
          {candidates.map((candidate, index) => (
            <ProductionCanvasCandidateItem
              key={`${candidate.asset_id}-${candidate.frame_index}`}
              busy={busyId !== null}
              canApprove={canApprove}
              canBranch={canBranch}
              canPlaceInTimeline={canDirectlyPlaceProductionCanvasVideo(node)}
              candidate={candidate}
              eager={index === 0}
              onApprove={onApprove}
              onBranch={onBranch}
              onPlaceInTimeline={onPlaceInTimeline}
              onReject={onReject}
              placed={
                node.outputs?.placed_media_asset_id === candidate.asset_id
              }
              selectedOutputId={selectedOutputId}
              staleImpact={staleImpact}
              timelineVersion={
                typeof node.outputs?.timeline_version === "number"
                  ? node.outputs.timeline_version
                  : undefined
              }
            />
          ))}
        </div>
      ) : busyId !== "load" ? (
        <p className="mt-2 text-xs leading-5 text-gray-500">暂无可评审候选。</p>
      ) : null}
      {error ? (
        <p className="mt-2 text-xs leading-5 text-red-600" role="alert">
          {error}
        </p>
      ) : null}
      {notice ? (
        <p className="mt-2 text-xs leading-5 text-blue-700" role="status">
          {notice}
        </p>
      ) : null}
    </section>
  );
}
