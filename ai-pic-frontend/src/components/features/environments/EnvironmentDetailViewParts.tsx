import {
  GenerationAuditWarnings,
  OperatorPanel,
  OperatorSectionHeader,
  OperatorState,
  StatusPill,
  operatorButtonClass,
} from "@/components/shared";
import type { Environment } from "@/utils/api/types";

interface EnvironmentDetailActionsProps {
  editing: boolean;
  saving: boolean;
  onEdit: () => void;
  onCancel: () => void;
  onSave: () => void;
}

export function EnvironmentDetailActions({
  editing,
  saving,
  onEdit,
  onCancel,
  onSave,
}: EnvironmentDetailActionsProps) {
  if (!editing) {
    return (
      <button
        type="button"
        onClick={onEdit}
        className={operatorButtonClass("primary")}
      >
        编辑资料
      </button>
    );
  }

  return (
    <div className="flex gap-2">
      <button
        type="button"
        onClick={onCancel}
        className={operatorButtonClass("secondary")}
      >
        取消
      </button>
      <button
        type="button"
        onClick={onSave}
        disabled={saving}
        className={operatorButtonClass("primary")}
      >
        {saving ? "保存中..." : "保存"}
      </button>
    </div>
  );
}

export function EnvironmentProductionNotice() {
  return (
    <OperatorState
      tone="blue"
      title="环境已接入 IP 中心"
      detail="环境可作为 IP 资产池的一部分，并在剧集 Timeline 中绑定到具体场景。"
    />
  );
}

export function EnvironmentAuditPanels({
  metadata,
}: {
  metadata?: Environment["metadata"];
}) {
  const envMeta = (metadata ?? {}) as Record<string, unknown>;
  const textToImageWarnings = (
    envMeta["last_text_to_image_generation"] as
      | Record<string, unknown>
      | undefined
  )?.["audit_warnings"];
  const imageToImageWarnings = (
    envMeta["last_image_to_image_generation"] as
      | Record<string, unknown>
      | undefined
  )?.["audit_warnings"];

  return (
    <div className="space-y-3">
      <GenerationAuditWarnings
        title="环境文生图提示"
        warnings={textToImageWarnings}
      />
      <GenerationAuditWarnings
        title="环境图生图提示"
        warnings={imageToImageWarnings}
      />
    </div>
  );
}

export function EnvironmentReadinessPanel({
  env,
  imageCount,
  onBack,
}: {
  env: Environment;
  imageCount: number;
  onBack: () => void;
}) {
  const linkedCount = env.linked_virtual_ip_count || 0;
  return (
    <OperatorPanel>
      <OperatorSectionHeader
        title="关联与生成状态"
        subtitle="IP 关联、图片池和生成任务"
      />
      <div className="space-y-4 p-4">
        <div className="flex items-center justify-between gap-3 text-xs">
          <span className="text-gray-500">IP 关联</span>
          <StatusPill tone={linkedCount > 0 ? "green" : "amber"}>
            {linkedCount > 0 ? `${linkedCount} 个 IP` : "未关联"}
          </StatusPill>
        </div>
        <div className="flex items-center justify-between gap-3 text-xs">
          <span className="text-gray-500">环境图片</span>
          <StatusPill tone={imageCount > 0 ? "green" : "gray"}>
            {imageCount > 0 ? "ready" : "empty"}
          </StatusPill>
        </div>
        <div className="flex items-center justify-between gap-3 text-xs">
          <span className="text-gray-500">生成入口</span>
          <StatusPill tone="blue">available</StatusPill>
        </div>
        <button
          type="button"
          onClick={onBack}
          className={operatorButtonClass("secondary", "w-full")}
        >
          返回环境列表
        </button>
      </div>
    </OperatorPanel>
  );
}

export function EnvironmentNotFound({ onBack }: { onBack: () => void }) {
  return (
    <OperatorState
      title="环境不存在或已删除"
      detail="返回列表后可以重新选择环境资产。"
      action={
        <button
          type="button"
          onClick={onBack}
          className={operatorButtonClass("secondary")}
        >
          返回列表
        </button>
      }
    />
  );
}
