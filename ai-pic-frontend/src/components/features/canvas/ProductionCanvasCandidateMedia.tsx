import Image from "next/image";
import type { ProductionCanvasMediaCandidate } from "@/utils/api/types";

export function ProductionCanvasCandidateMedia({
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
