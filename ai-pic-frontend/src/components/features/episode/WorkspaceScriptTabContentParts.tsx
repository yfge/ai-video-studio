"use client";

import {
  ModelSelector,
  OperatorModalFrame,
  OperatorTabs,
  OperatorToolbar,
  operatorButtonClass,
} from "@/components/shared";

type ScriptSubTab = "overview" | "scenes";

export function ScriptTabToolbar({
  activeSubTab,
  setActiveSubTab,
  onOpenRegenerate,
  regenerating,
  canRegenerate,
}: {
  activeSubTab: ScriptSubTab;
  setActiveSubTab: (tab: ScriptSubTab) => void;
  onOpenRegenerate: () => void;
  regenerating?: boolean;
  canRegenerate: boolean;
}) {
  return (
    <OperatorToolbar>
      <OperatorTabs
        tabs={[
          { key: "overview", label: "概览" },
          { key: "scenes", label: "场景" },
        ]}
        active={activeSubTab}
        onChange={setActiveSubTab}
      />
      {canRegenerate ? (
        <button
          type="button"
          onClick={onOpenRegenerate}
          disabled={regenerating}
          className={operatorButtonClass("secondary")}
        >
          {regenerating ? "重新生成中..." : "重新生成剧本"}
        </button>
      ) : null}
    </OperatorToolbar>
  );
}

export function ScriptRegenerateModal({
  open,
  model,
  setModel,
  regenerating,
  onCancel,
  onConfirm,
}: {
  open: boolean;
  model: string;
  setModel: (model: string) => void;
  regenerating?: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  if (!open) return null;
  return (
    <OperatorModalFrame
      title="重新生成剧本"
      subtitle="使用最新分类优化创建新的剧本内容"
      footer={
        <>
          <button
            type="button"
            onClick={onCancel}
            className={operatorButtonClass("secondary")}
          >
            取消
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={regenerating}
            className={operatorButtonClass("primary")}
          >
            确认重新生成
          </button>
        </>
      }
    >
      <ModelSelector
        value={model}
        onChange={setModel}
        label="选择模型"
        helperText="留空使用原有模型设置"
        allowAuto
        autoLabel="使用原有模型"
        modelType="text"
      />
    </OperatorModalFrame>
  );
}
