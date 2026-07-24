import { StatusPill, operatorButtonClass } from "@/components/shared";
import type { Story } from "@/utils/api/types";

export function StorySeedPlanningStatus(props: {
  taskId: number | null;
  taskStatus: string | null;
  active: boolean;
  requesting: boolean;
  progress: string;
  error: string;
  onCancel: () => void;
}) {
  return (
    <>
      {props.taskId ? (
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <StatusPill
            tone={props.taskStatus === "completed" ? "green" : "blue"}
          >
            规划任务 #{props.taskId} · {props.taskStatus}
          </StatusPill>
          {props.active ? (
            <button
              type="button"
              disabled={props.requesting}
              onClick={props.onCancel}
              className={operatorButtonClass("secondary")}
            >
              取消规划
            </button>
          ) : null}
        </div>
      ) : null}
      {props.progress ? (
        <p className="text-xs text-gray-500">{props.progress}</p>
      ) : null}
      {props.error ? (
        <p role="alert" className="text-xs text-red-600">
          {props.error}
        </p>
      ) : null}
    </>
  );
}

export function StorySeedSaveActions(props: {
  saving: boolean;
  disabled: boolean;
  canConfirm: boolean;
  onSave: (status: "draft" | "confirmed") => Promise<void>;
}) {
  return (
    <div className="flex flex-wrap justify-end gap-2 border-t border-gray-100 pt-4">
      <span className="mr-auto text-xs text-gray-500">
        保存与确认不调用模型；确认后章节计划冻结。
      </span>
      <button
        type="button"
        disabled={props.saving || props.disabled}
        onClick={() => void props.onSave("draft")}
        className={operatorButtonClass("secondary")}
      >
        保存大纲
      </button>
      <button
        type="button"
        disabled={props.saving || props.disabled || !props.canConfirm}
        onClick={() => void props.onSave("confirmed")}
        className={operatorButtonClass("primary")}
      >
        确认 Story Seed
      </button>
    </div>
  );
}

export function StorySeedBaselineEvidence({ story }: { story: Story }) {
  const downstream = story.extra_metadata?.story_seed_downstream as
    | { status?: string }
    | undefined;
  return (
    <div className="flex flex-wrap gap-2 text-xs">
      <StatusPill tone="blue">
        公共记忆基线 v{story.shared_memory_baseline_version || 0}
      </StatusPill>
      <StatusPill tone="gray">Seed v{story.story_seed_version || 1}</StatusPill>
      {downstream?.status === "review_required" ? (
        <StatusPill tone="amber">下游待复核</StatusPill>
      ) : null}
    </div>
  );
}
