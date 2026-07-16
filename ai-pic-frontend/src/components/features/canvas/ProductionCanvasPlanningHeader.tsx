import type { ComponentProps } from "react";
import Link from "next/link";
import {
  OperatorSectionHeader,
  operatorButtonClass,
} from "@/components/shared";
import { ProductionCanvasChatBar } from "./ProductionCanvasChatBar";

type ChatBarProps = ComponentProps<typeof ProductionCanvasChatBar>;

export function ProductionCanvasPlanningHeader(props: ChatBarProps) {
  const singleVideo = props.creationMode === "single_video";
  return (
    <>
      <OperatorSectionHeader
        title={singleVideo ? "单条视频生产" : "短剧生产链路"}
        subtitle={
          singleVideo
            ? "视频目标 -> Script -> Audio + Timeline；图片、视频候选和渲染继续由操作员显式触发"
            : "Brief -> Script -> Audio + Timeline -> Storyboard Support -> Image Candidates -> Video Candidates -> Render -> Export -> Report"
        }
        action={
          <Link href="/tasks" className={operatorButtonClass("ghost")}>
            查看任务
          </Link>
        }
      />
      <ProductionCanvasChatBar {...props} />
    </>
  );
}
