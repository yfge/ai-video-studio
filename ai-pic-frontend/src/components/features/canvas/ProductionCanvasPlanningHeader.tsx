import type { ComponentProps, ReactNode } from "react";
import { ProductionCanvasChatBar } from "./ProductionCanvasChatBar";

type ChatBarProps = ComponentProps<typeof ProductionCanvasChatBar>;

export function ProductionCanvasPlanningHeader({
  advancedControls,
  ...props
}: ChatBarProps & { advancedControls?: ReactNode }) {
  const singleVideo = props.creationMode === "single_video";
  return (
    <>
      <div className="sr-only">
        <h2>{singleVideo ? "单条视频生产" : "短剧生产链路"}</h2>
        <p>
          {singleVideo
            ? "视频目标 -> Script -> Audio + Timeline；图片、视频候选和渲染继续由操作员显式触发"
            : "Brief -> Script -> Audio + Timeline -> Storyboard Support -> Image Candidates -> Video Candidates -> Render -> Export -> Report"}
        </p>
      </div>
      <ProductionCanvasChatBar {...props} advancedControls={advancedControls} />
    </>
  );
}
