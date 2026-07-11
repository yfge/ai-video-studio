import type { ComponentProps } from "react";
import Link from "next/link";
import {
  OperatorSectionHeader,
  operatorButtonClass,
} from "@/components/shared";
import { ProductionCanvasChatBar } from "./ProductionCanvasChatBar";

type ChatBarProps = ComponentProps<typeof ProductionCanvasChatBar>;

export function ProductionCanvasPlanningHeader(props: ChatBarProps) {
  return (
    <>
      <OperatorSectionHeader
        title="短剧生产链路"
        subtitle="Brief -> Script -> Audio + Timeline -> Storyboard Support -> Image Candidates -> Video Candidates -> Render -> Export -> Report"
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
