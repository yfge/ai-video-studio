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

export function EnvironmentMigrationNotice() {
  return (
    <OperatorState
      tone="amber"
      title="环境资产迁移中"
      detail="环境资产暂未完全迁移到 IP 生产链路；当前页面继续作为环境图片、生成参数和任务状态的工作区。"
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
  imageCount,
  onBack,
}: {
  imageCount: number;
  onBack: () => void;
}) {
  return (
    <OperatorPanel>
      <OperatorSectionHeader
        title="迁移与生成状态"
        subtitle="详情、图片池和生成任务保持现有业务逻辑"
      />
      <div className="space-y-4 p-4">
        <div className="flex items-center justify-between gap-3 text-xs">
          <span className="text-gray-500">IP 生产链路</span>
          <StatusPill tone="amber">迁移中</StatusPill>
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
