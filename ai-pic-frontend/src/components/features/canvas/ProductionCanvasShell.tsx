import { OperatorShell } from "@/components/shared";
import { ProductionCanvasBackLink } from "./ProductionCanvasBackLink";
import { ProductionCanvasContent } from "./ProductionCanvasBoard";

export function ProductionCanvasShell({
  blank = false,
  initialRunId,
}: {
  blank?: boolean;
  initialRunId?: string | null;
}) {
  return (
    <OperatorShell
      title="创作画布"
      subtitle="从现有项目编排剧本、分镜、图片候选、视频候选和时间线"
      breadcrumb={["IP 中心", "创作画布"]}
      showGlobalSearch={false}
      rightSlot={<ProductionCanvasBackLink />}
    >
      <ProductionCanvasContent
        blank={blank}
        initialRunId={initialRunId}
        initialView="execution"
        storageKey={blank ? null : undefined}
      />
    </OperatorShell>
  );
}
