import { useCallback, useEffect, useState } from "react";
import { productionCanvasAPI } from "@/utils/api/endpoints";
import type {
  ProductionCanvasMediaCandidate,
  ProductionCanvasResolvedContext,
  ProductionCanvasStaleImpactNode,
} from "@/utils/api/types";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import type { ProductionCanvasState } from "./productionCanvasState";
import type { ProductionCanvasStateIdentity } from "./productionCanvasStateIdentity";
import {
  ProductionCanvasCandidateReviewPanel,
  type ProductionCanvasCandidateBusyId,
} from "./ProductionCanvasCandidateReviewPanel";
import { loadProductionCanvasCandidates } from "./productionCanvasCandidateLoading";
import { useProductionCanvasCandidateRequestGuard } from "./useProductionCanvasCandidateRequestGuard";

function isReviewNode(node?: ProductionCanvasNode) {
  return (
    node?.skill === "image.candidates" || node?.skill === "video.candidates"
  );
}

export function ProductionCanvasCandidateReview({
  canApprove = true,
  canBranch = true,
  captureCanvasStateIdentity,
  node,
  onCanvasStateUpdated,
  onDomainContextResolved,
  runId,
}: {
  canApprove?: boolean;
  canBranch?: boolean;
  captureCanvasStateIdentity: () => ProductionCanvasStateIdentity;
  node?: ProductionCanvasNode;
  onCanvasStateUpdated: (
    state: ProductionCanvasState,
    identity: ProductionCanvasStateIdentity,
  ) => boolean;
  onDomainContextResolved?: (context: ProductionCanvasResolvedContext) => void;
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
  const [busyId, setBusyId] = useState<ProductionCanvasCandidateBusyId>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const {
    adoptRunState,
    captureRequest,
    invalidateRequests,
    isCurrentRequest,
    isLatestRequest,
    reportError,
  } = useProductionCanvasCandidateRequestGuard({
    captureCanvasStateIdentity,
    onCanvasStateUpdated,
    runId,
    setError,
  });
  const load = useCallback(async () => {
    if (!nodeId || !runId || !reviewable) return;
    const request = captureRequest();
    if (!request) return;
    setBusyId("load");
    setError(null);
    try {
      const response = await loadProductionCanvasCandidates(runId, nodeId);
      if (!response.success || !response.data) {
        throw new Error(response.error || "候选加载失败");
      }
      if (!isCurrentRequest(request)) return;
      setCandidates(
        Array.isArray(response.data.candidates) ? response.data.candidates : [],
      );
      setSelectedOutputId(response.data.selected_output_id || null);
      setStaleImpact(response.data.stale_impact || []);
    } catch (cause) {
      reportError(cause, request);
    } finally {
      if (isLatestRequest(request)) setBusyId(null);
    }
  }, [
    captureRequest,
    isCurrentRequest,
    isLatestRequest,
    nodeId,
    reportError,
    reviewable,
    runId,
  ]);

  useEffect(() => {
    invalidateRequests();
    setCandidates([]);
    setSelectedOutputId(null);
    setStaleImpact([]);
    setError(null);
    setNotice(null);
    setBusyId(null);
    void load();
  }, [invalidateRequests, load]);

  if (!node || !runId || !isReviewNode(node)) return null;

  const approve = async (candidate: ProductionCanvasMediaCandidate) => {
    const request = captureRequest();
    if (!request) return;
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
      if (!adoptRunState(response.data, request)) return;
      if (!isLatestRequest(request)) return;
      setCandidates((current) =>
        current.map((item) => ({
          ...item,
          selected: item.asset_id === candidate.asset_id,
        })),
      );
      setSelectedOutputId(candidate.asset_id);
      if (!selectedOutputId) await load();
    } catch (cause) {
      reportError(cause, request);
    } finally {
      if (isLatestRequest(request)) setBusyId(null);
    }
  };

  const reject = async (
    candidate: ProductionCanvasMediaCandidate,
    reason: string,
  ) => {
    const request = captureRequest();
    if (!request) return;
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
      if (!adoptRunState(response.data, request)) return;
      if (!isLatestRequest(request)) return;
      await load();
    } catch (cause) {
      reportError(cause, request);
    } finally {
      if (isLatestRequest(request)) setBusyId(null);
    }
  };

  const branch = async (
    candidate: ProductionCanvasMediaCandidate,
    instruction: string,
  ) => {
    const request = captureRequest();
    if (!request) return;
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
      if (!adoptRunState(response.data, request)) return;
      if (!isLatestRequest(request)) return;
      setNotice(`已从候选 #${candidate.asset_id} 提交分支生成任务。`);
    } catch (cause) {
      reportError(cause, request);
    } finally {
      if (isLatestRequest(request)) setBusyId(null);
    }
  };

  const placeInTimeline = async () => {
    const expectedVersion = node.outputs?.timeline_version;
    if (typeof expectedVersion !== "number") return;
    const request = captureRequest();
    if (!request) return;
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
      if (!adoptRunState(response.data, request)) return;
      if (response.data.resolved_context) {
        onDomainContextResolved?.(response.data.resolved_context);
      }
    } catch (cause) {
      reportError(cause, request);
    } finally {
      if (isLatestRequest(request)) setBusyId(null);
    }
  };

  return (
    <ProductionCanvasCandidateReviewPanel
      busyId={busyId}
      canApprove={canApprove}
      canBranch={canBranch}
      candidates={candidates}
      error={error}
      node={node}
      notice={notice}
      onApprove={(item) => void approve(item)}
      onBranch={(item, instruction) => void branch(item, instruction)}
      onPlaceInTimeline={() => void placeInTimeline()}
      onRefresh={() => void load()}
      onReject={(item, reason) => void reject(item, reason)}
      selectedOutputId={selectedOutputId}
      staleImpact={staleImpact}
    />
  );
}
