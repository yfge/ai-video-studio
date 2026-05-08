"use client";

import {
  OperatorPanel,
  OperatorSectionHeader,
  operatorButtonClass,
} from "@/components/shared";

interface WorkflowStepsProps {
  onGoToSceneDetails: () => void;
  onGoToSceneStructure: () => void;
  onGoToStoryboard: () => void;
}

export function WorkflowSteps({
  onGoToSceneDetails,
  onGoToSceneStructure,
  onGoToStoryboard,
}: WorkflowStepsProps) {
  return (
    <OperatorPanel>
      <OperatorSectionHeader title="生产入口" subtitle="文本、结构和分镜入口统一归档" />
      <div className="grid gap-3 p-4 md:grid-cols-3">
        <StepCard label="场景文本详情" detail="浏览对白与舞台指令。" onClick={onGoToSceneDetails} />
        <StepCard label="结构化场景 / 镜头" detail="调整节拍与镜头顺序。" onClick={onGoToSceneStructure} />
        <StepCard label="分镜管理" detail="进入分镜工作台。" onClick={onGoToStoryboard} />
      </div>
    </OperatorPanel>
  );
}

function StepCard({
  label,
  detail,
  onClick,
}: {
  label: string;
  detail: string;
  onClick: () => void;
}) {
  return (
    <div className="rounded-md border border-gray-200 bg-gray-50 p-3">
      <div className="text-sm font-medium text-gray-950">{label}</div>
      <p className="mt-1 text-xs text-gray-500">{detail}</p>
      <button
        type="button"
        onClick={onClick}
        className={operatorButtonClass("secondary", "mt-3")}
      >
        打开
      </button>
    </div>
  );
}
