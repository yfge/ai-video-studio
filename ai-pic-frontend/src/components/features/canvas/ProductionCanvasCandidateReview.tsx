import Image from "next/image";
import { useCallback, useEffect, useState } from "react";
import { operatorButtonClass } from "@/components/shared";
import { productionCanvasAPI } from "@/utils/api/endpoints";
import type { ProductionCanvasMediaCandidate } from "@/utils/api/types";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { productionCanvasStateFromRun } from "./productionCanvasPersistence";
import type { ProductionCanvasState } from "./productionCanvasState";

function isReviewNode(node?: ProductionCanvasNode) {
  return (
    node?.skill === "image.candidates" || node?.skill === "video.candidates"
  );
}

function CandidateMedia({
  candidate,
  eager,
}: {
  candidate: ProductionCanvasMediaCandidate;
  eager?: boolean;
}) {
  const label = `${candidate.media_type === "image" ? "图片" : "视频"}候选 ${
    candidate.frame_index + 1
  }`;
  return (
    <div className="relative aspect-video w-full overflow-hidden bg-gray-950">
      {candidate.media_type === "image" ? (
        <Image
          alt={label}
          className="object-contain"
          fill
          loading={eager ? "eager" : "lazy"}
          sizes="248px"
          src={candidate.url}
          unoptimized
        />
      ) : (
        <video
          aria-label={label}
          className="h-full w-full object-contain"
          controls
          preload="metadata"
          src={candidate.url}
        />
      )}
    </div>
  );
}

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

export function ProductionCanvasCandidateReview({
  node,
  onCanvasStateUpdated,
  runId,
}: {
  node?: ProductionCanvasNode;
  onCanvasStateUpdated: (state: ProductionCanvasState) => void;
  runId: string;
}) {
  const [candidates, setCandidates] = useState<
    ProductionCanvasMediaCandidate[]
  >([]);
  const [busyId, setBusyId] = useState<number | "load" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!node || !runId || !isReviewNode(node)) return;
    setBusyId("load");
    setError(null);
    try {
      const response = await productionCanvasAPI.getNodeCandidates(
        runId,
        node.id,
      );
      if (!response.success || !response.data) {
        throw new Error(response.error || "候选加载失败");
      }
      setCandidates(
        Array.isArray(response.data.candidates) ? response.data.candidates : [],
      );
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusyId(null);
    }
  }, [node, runId]);

  useEffect(() => {
    setCandidates([]);
    setError(null);
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
            <article
              key={`${candidate.asset_id}-${candidate.frame_index}`}
              className="py-3"
            >
              <CandidateMedia candidate={candidate} eager={index === 0} />
              <div className="mt-2 text-[11px] leading-4 text-gray-500">
                {candidateSummary(candidate)}
              </div>
              <div className="mt-2 flex items-center justify-between gap-2">
                <a
                  className="truncate text-xs font-medium text-blue-700 hover:underline"
                  href={candidate.url}
                  rel="noreferrer"
                  target="_blank"
                >
                  查看原始资产
                </a>
                <button
                  type="button"
                  className={operatorButtonClass(
                    candidate.selected ? "secondary" : "primary",
                    "h-8 shrink-0 px-3 text-xs",
                  )}
                  disabled={candidate.selected || busyId !== null}
                  onClick={() => void approve(candidate)}
                >
                  {candidate.selected
                    ? "已选用"
                    : busyId === candidate.asset_id
                    ? "选用中"
                    : "选用"}
                </button>
              </div>
            </article>
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
    </section>
  );
}
