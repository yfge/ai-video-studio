import Image from "next/image";
import { useState } from "react";
import { operatorButtonClass } from "@/components/shared";
import type {
  ProductionCanvasMediaCandidate,
  ProductionCanvasStaleImpactNode,
} from "@/utils/api/types";

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

export function ProductionCanvasCandidateItem({
  busy,
  candidate,
  eager,
  onApprove,
  onPlaceInTimeline,
  placed,
  selectedOutputId,
  staleImpact,
  timelineVersion,
}: {
  busy: boolean;
  candidate: ProductionCanvasMediaCandidate;
  eager?: boolean;
  onApprove: (candidate: ProductionCanvasMediaCandidate) => void;
  onPlaceInTimeline: () => void;
  placed: boolean;
  selectedOutputId?: number | null;
  staleImpact: ProductionCanvasStaleImpactNode[];
  timelineVersion?: number;
}) {
  const [confirming, setConfirming] = useState(false);
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
      <CandidateMedia candidate={candidate} eager={eager} />
      <div className="mt-2 text-[11px] leading-4 text-gray-500">
        {candidateSummary(candidate)}
      </div>
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
          disabled={candidate.selected || busy}
          onClick={approve}
        >
          {candidate.selected ? "已选用" : busy ? "选用中" : "选用"}
        </button>
      </div>
      {candidate.media_type === "video" && candidate.selected ? (
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
