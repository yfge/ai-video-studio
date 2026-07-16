import { useRef, useState } from "react";
import { operatorButtonClass } from "@/components/shared";
import type {
  ProductionCanvasMediaCandidate,
  ProductionCanvasStaleImpactNode,
} from "@/utils/api/types";
import { ProductionCanvasCandidateBranchControls } from "./ProductionCanvasCandidateBranchControls";
import { ProductionCanvasCandidateMedia } from "./ProductionCanvasCandidateMedia";

function candidateSummary(candidate: ProductionCanvasMediaCandidate) {
  return [
    `帧 ${candidate.frame_index + 1}`,
    candidate.clip_id ? `Clip ${candidate.clip_id}` : null,
    candidate.model || null,
    candidate.duration_seconds
      ? `${candidate.duration_seconds.toFixed(1)}s`
      : null,
  ]
    .filter(Boolean)
    .join(" · ");
}

export function ProductionCanvasCandidateItem({
  busy,
  canApprove = true,
  canBranch = true,
  canPlaceInTimeline,
  candidate,
  eager,
  onApprove,
  onBranch,
  onPlaceInTimeline,
  onReject,
  placed,
  selectedOutputId,
  staleImpact,
  timelineVersion,
}: {
  busy: boolean;
  canApprove?: boolean;
  canBranch?: boolean;
  canPlaceInTimeline: boolean;
  candidate: ProductionCanvasMediaCandidate;
  eager?: boolean;
  onApprove: (candidate: ProductionCanvasMediaCandidate) => void;
  onBranch: (
    candidate: ProductionCanvasMediaCandidate,
    instruction: string,
  ) => void;
  onPlaceInTimeline: () => void;
  onReject: (candidate: ProductionCanvasMediaCandidate, reason: string) => void;
  placed: boolean;
  selectedOutputId?: number | null;
  staleImpact: ProductionCanvasStaleImpactNode[];
  timelineVersion?: number;
}) {
  const [confirming, setConfirming] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const rejectionReasonRef = useRef<HTMLTextAreaElement>(null);
  const switchingSelection = Boolean(
    selectedOutputId && selectedOutputId !== candidate.asset_id,
  );
  const approve = () => {
    if (switchingSelection && staleImpact.length && !confirming) {
      setConfirming(true);
      return;
    }
    setConfirming(false);
    onApprove(candidate);
  };
  return (
    <article className="py-3">
      <ProductionCanvasCandidateMedia candidate={candidate} eager={eager} />
      <div className="mt-2 text-[11px] leading-4 text-gray-500">
        {candidateSummary(candidate)}
      </div>
      {candidate.review_state === "rejected" ? (
        <div className="mt-2 border-l-2 border-red-400 bg-red-50 px-3 py-2 text-xs leading-5 text-red-900">
          <span className="font-semibold">已拒绝</span>
          {candidate.rejection_reason
            ? ` · ${candidate.rejection_reason}`
            : null}
        </div>
      ) : null}
      {candidate.parent_candidate_id ? (
        <div className="mt-2 border-l-2 border-blue-300 bg-blue-50 px-3 py-2 text-xs leading-5 text-blue-950">
          分支自候选 #{candidate.parent_candidate_id}
          {candidate.branch_task_id
            ? ` · Task #${candidate.branch_task_id}`
            : null}
          {candidate.branch_instruction
            ? ` · ${candidate.branch_instruction}`
            : null}
        </div>
      ) : null}
      {confirming ? (
        <div className="mt-2 border-l-2 border-amber-400 bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-950">
          <p className="font-semibold">切换后以下节点将标记为已过期：</p>
          <p>{staleImpact.map((item) => item.title).join("、")}</p>
          <div className="mt-2 flex justify-end gap-2">
            <button
              type="button"
              className={operatorButtonClass("ghost", "h-7 px-2 text-xs")}
              onClick={() => setConfirming(false)}
            >
              取消
            </button>
            <button
              type="button"
              className={operatorButtonClass("primary", "h-7 px-2 text-xs")}
              onClick={approve}
            >
              确认切换
            </button>
          </div>
        </div>
      ) : null}
      {rejecting ? (
        <div className="mt-2 border-l-2 border-gray-300 bg-gray-50 px-3 py-2">
          <label
            className="block text-xs font-medium text-gray-700"
            htmlFor={`candidate-rejection-${candidate.asset_id}`}
          >
            拒绝原因（可选）
          </label>
          <textarea
            id={`candidate-rejection-${candidate.asset_id}`}
            className="mt-1 min-h-16 w-full resize-y border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-900 outline-none focus:border-blue-500"
            maxLength={500}
            ref={rejectionReasonRef}
          />
          <div className="mt-2 flex justify-end gap-2">
            <button
              type="button"
              className={operatorButtonClass("ghost", "h-7 px-2 text-xs")}
              onClick={() => setRejecting(false)}
            >
              取消
            </button>
            <button
              type="button"
              className={operatorButtonClass("danger", "h-7 px-2 text-xs")}
              onClick={() => {
                setRejecting(false);
                onReject(candidate, rejectionReasonRef.current?.value || "");
              }}
            >
              确认拒绝
            </button>
          </div>
        </div>
      ) : null}
      <div className="mt-2 flex items-center justify-between gap-2">
        <a
          className="truncate text-xs font-medium text-blue-700 hover:underline"
          href={candidate.url}
          rel="noreferrer"
          target="_blank"
        >
          查看原始资产
        </a>
        <div className="flex shrink-0 items-center gap-1">
          {canBranch ? (
            <ProductionCanvasCandidateBranchControls
              busy={busy}
              candidateId={candidate.asset_id}
              onBranch={(instruction) => onBranch(candidate, instruction)}
            />
          ) : null}
          {canApprove ? (
            <>
              <button
                type="button"
                className={operatorButtonClass(
                  "ghost",
                  "h-8 px-2 text-xs text-red-700",
                )}
                disabled={busy}
                onClick={() => setRejecting(true)}
              >
                拒绝
              </button>
              <button
                type="button"
                className={operatorButtonClass(
                  candidate.selected ? "secondary" : "primary",
                  "h-8 px-3 text-xs",
                )}
                disabled={candidate.selected || busy}
                onClick={approve}
              >
                {candidate.selected
                  ? "已选用"
                  : busy
                  ? "选用中"
                  : candidate.review_state === "rejected"
                  ? "重新选用"
                  : "选用"}
              </button>
            </>
          ) : null}
        </div>
      </div>
      {canApprove &&
      canPlaceInTimeline &&
      candidate.media_type === "video" &&
      candidate.selected ? (
        <button
          type="button"
          className={operatorButtonClass(
            "primary",
            "mt-2 h-8 w-full px-3 text-xs",
          )}
          disabled={busy || timelineVersion === undefined || placed}
          onClick={onPlaceInTimeline}
        >
          {placed
            ? `已放入 Timeline v${timelineVersion}`
            : busy
            ? "写入中"
            : "放入 Timeline"}
        </button>
      ) : null}
    </article>
  );
}
