import { useCallback, useEffect, useState } from "react";
import { operatorButtonClass } from "@/components/shared";
import { productionCanvasAPI } from "@/utils/api/endpoints";
import type {
  ProductionCanvasMediaCandidate,
  ProductionCanvasStaleImpactNode,
} from "@/utils/api/types";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { productionCanvasStateFromRun } from "./productionCanvasPersistence";
import type { ProductionCanvasState } from "./productionCanvasState";
import { ProductionCanvasCandidateItem } from "./ProductionCanvasCandidateItem";

function isReviewNode(node?: ProductionCanvasNode) {
  return (
    node?.skill === "image.candidates" || node?.skill === "video.candidates"
  );
}

export function ProductionCanvasCandidateReview({
  canApprove = true,
  canBranch = true,
  node,
  onCanvasStateUpdated,
  runId,
}: {
  canApprove?: boolean;
  canBranch?: boolean;
  node?: ProductionCanvasNode;
  onCanvasStateUpdated: (state: ProductionCanvasState) => void;
  runId: string;
}) {
  const nodeId = node?.id;
  const reviewable = isReviewNode(node);
  const [candidates, setCandidates] = useState<
    ProductionCanvasMediaCandidate[]
  >([]);
  const [selectedOutputId, setSelectedOutputId] = useState<number | null>(null);
  const [staleImpact, setStaleImpact] = useState<
    ProductionCanvasStaleImpactNode[]
  >([]);
  const [busyId, setBusyId] = useState<number | "load" | "place" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!nodeId || !runId || !reviewable) return;
    setBusyId("load");
    setError(null);
    try {
      const response = await productionCanvasAPI.getNodeCandidates(
        runId,
        nodeId,
      );
      if (!response.success || !response.data) {
        throw new Error(response.error || "候选加载失败");
      }
      setCandidates(
        Array.isArray(response.data.candidates) ? response.data.candidates : [],
      );
      setSelectedOutputId(response.data.selected_output_id || null);
      setStaleImpact(response.data.stale_impact || []);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusyId(null);
    }
  }, [nodeId, reviewable, runId]);

  useEffect(() => {
    setCandidates([]);
    setSelectedOutputId(null);
    setStaleImpact([]);
    setError(null);
    setNotice(null);
    void load();
  }, [load]);

  if (!node || !runId || !isReviewNode(node)) return null;

  const approve = async (candidate: ProductionCanvasMediaCandidate) => {
    setBusyId(candidate.asset_id);
    setError(null);
    try {
      const response = await productionCanvasAPI.approveNodeCandidate(
        runId,
        node.id,
        candidate.asset_id,
      );
      if (!response.success || !response.data) {
        throw new Error(response.error || "候选选用失败");
      }
      setCandidates((current) =>
        current.map((item) => ({
          ...item,
          selected: item.asset_id === candidate.asset_id,
        })),
      );
      setSelectedOutputId(candidate.asset_id);
      onCanvasStateUpdated(productionCanvasStateFromRun(response.data));
      if (!selectedOutputId) await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusyId(null);
    }
  };

  const reject = async (
    candidate: ProductionCanvasMediaCandidate,
    reason: string,
  ) => {
    setBusyId(candidate.asset_id);
    setError(null);
    try {
      const response = await productionCanvasAPI.rejectNodeCandidate(
        runId,
        node.id,
        candidate.asset_id,
        reason.trim(),
      );
      if (!response.success || !response.data) {
        throw new Error(response.error || "候选拒绝失败");
      }
      onCanvasStateUpdated(productionCanvasStateFromRun(response.data));
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusyId(null);
    }
  };

  const branch = async (
    candidate: ProductionCanvasMediaCandidate,
    instruction: string,
  ) => {
    setBusyId(candidate.asset_id);
    setError(null);
    setNotice(null);
    try {
      const response = await productionCanvasAPI.branchNodeCandidate(
        runId,
        node.id,
        candidate.asset_id,
        instruction.trim(),
      );
      if (!response.success || !response.data) {
        throw new Error(response.error || "候选分支生成失败");
      }
      onCanvasStateUpdated(productionCanvasStateFromRun(response.data));
      setNotice(`已从候选 #${candidate.asset_id} 提交分支生成任务。`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusyId(null);
    }
  };

  const placeInTimeline = async () => {
    const expectedVersion = node.outputs?.timeline_version;
    if (typeof expectedVersion !== "number") return;
    setBusyId("place");
    setError(null);
    try {
      const response = await productionCanvasAPI.placeNodeVideoInTimeline(
        runId,
        node.id,
        expectedVersion,
      );
      if (!response.success || !response.data) {
        throw new Error(response.error || "放入 Timeline 失败");
      }
      onCanvasStateUpdated(productionCanvasStateFromRun(response.data));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusyId(null);
    }
  };

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
          onClick={() => void load()}
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
              candidate={candidate}
              eager={index === 0}
              onApprove={(item) => void approve(item)}
              onBranch={(item, instruction) => void branch(item, instruction)}
              onPlaceInTimeline={() => void placeInTimeline()}
              onReject={(item, reason) => void reject(item, reason)}
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
