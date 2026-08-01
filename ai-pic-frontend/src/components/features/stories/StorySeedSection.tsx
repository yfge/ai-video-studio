"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  OperatorPanel,
  OperatorSectionHeader,
  StatusPill,
  operatorButtonClass,
} from "@/components/shared";
import { storyAPI } from "@/utils/api/endpoints";
import type { Story } from "@/utils/api/types";
import { saveStructuredStorySeed } from "@/utils/api/endpoints";
import { useStorySeedStructureTask } from "@/hooks/useStorySeedStructureTask";
import {
  resolveStorySeed,
  StorySeedEditor,
  StorySeedView,
  storySeedOutlineText,
} from "./StorySeedFields";
import { StoryStructuredOutlineEditor } from "./StoryStructuredOutlineEditor";
import { validateStructuredOutline } from "./storyStructuredOutline";
import {
  StorySeedBaselineEvidence,
  StorySeedPlanningStatus,
  StorySeedSaveActions,
} from "./StorySeedSectionControls";
import {
  StorySeedPlanningAction,
  StorySeedPlanningInputs,
  suggestedStructureChapterCount,
  suggestedStructureModel,
} from "./StorySeedPlanningInputs";

export function StorySeedSection({
  story,
  locked = false,
  onChanged,
}: {
  story: Story;
  locked?: boolean;
  onChanged?: () => Promise<void>;
}) {
  const initial = useMemo(() => resolveStorySeed(story), [story]);
  const [seed, setSeed] = useState(initial);
  const [status, setStatus] = useState<"draft" | "confirmed">(
    story.story_seed_status === "confirmed" ? "confirmed" : "draft",
  );
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");
  const [planningChapterCount, setPlanningChapterCount] = useState(
    suggestedStructureChapterCount(initial),
  );
  const [planningModel, setPlanningModel] = useState(
    suggestedStructureModel(initial, story.ai_model),
  );
  const completedTask = useRef<number | null>(null);
  const acceptPlannedStory = useCallback((next: Story) => {
    if (next.story_seed) setSeed(next.story_seed);
    setStatus(next.story_seed_status === "confirmed" ? "confirmed" : "draft");
  }, []);
  const planning = useStorySeedStructureTask(story, acceptPlannedStory);
  useEffect(() => {
    setSeed(initial);
    setStatus(story.story_seed_status === "confirmed" ? "confirmed" : "draft");
    setPlanningChapterCount(suggestedStructureChapterCount(initial));
    setPlanningModel(suggestedStructureModel(initial, story.ai_model));
  }, [initial, story.ai_model, story.story_seed_status]);
  useEffect(() => {
    if (
      planning.taskId &&
      ["completed", "failed", "cancelled"].includes(
        planning.taskStatus || "",
      ) &&
      completedTask.current !== planning.taskId
    ) {
      completedTask.current = planning.taskId;
      void onChanged?.();
    }
  }, [onChanged, planning.taskId, planning.taskStatus]);

  const save = async (nextStatus: "draft" | "confirmed") => {
    try {
      setSaving(true);
      const response =
        seed.schema === "story_seed_v2"
          ? await saveStructuredStorySeed(story.business_id, {
              outline_text: storySeedOutlineText(seed),
              structured_outline: {
                ...seed.structured_outline,
                status: nextStatus,
              },
              story_seed_status: nextStatus,
              story_seed_version:
                story.story_seed_version || seed.structured_outline.version,
            })
          : await storyAPI.updateStory(story.business_id, {
              story_seed: seed,
              story_seed_status: nextStatus,
            });
      if (!response.success || !response.data) throw new Error(response.error);
      setSeed(response.data.story_seed || seed);
      setStatus(
        response.data.story_seed_status === "confirmed"
          ? "confirmed"
          : nextStatus,
      );
      setEditing(false);
      setNotice(
        nextStatus === "confirmed"
          ? "结构化 Story Seed 已确认并冻结；不会自动生成正文"
          : "Story Seed 已本地保存；未调用模型",
      );
      await onChanged?.();
    } catch (error) {
      setNotice(`保存失败：${String(error)}`);
    } finally {
      setSaving(false);
    }
  };
  const structured =
    seed.schema === "story_seed_v2" ? seed.structured_outline : null;
  const validation = structured ? validateStructuredOutline(structured) : null;
  const controlsLocked = locked || planning.active;
  const planningDisabled = controlsLocked || planning.requesting;
  const showPlanning =
    !structured || structured.thread_schedule_version !== 1 || editing;
  const planningInputError = !Number.isInteger(planningChapterCount)
    ? "结构化章节数必须是有限正整数"
    : !planningModel.trim()
    ? "请选择结构化规划模型"
    : "";
  const startPlanning = () => {
    if (planningInputError) {
      setNotice(planningInputError);
      return;
    }
    void planning.start({
      chapter_count: planningChapterCount,
      model: planningModel.trim(),
    });
  };
  const toggleEditing = () => {
    if (controlsLocked) return;
    if (status === "confirmed" && seed.schema === "story_seed_v2") {
      setSeed({
        ...seed,
        structured_outline: { ...seed.structured_outline, status: "draft" },
      });
      setStatus("draft");
      setEditing(true);
      setNotice("已进入新草稿；保存并重新确认后才可生成正文");
      return;
    }
    setEditing((value) => !value);
  };

  return (
    <OperatorPanel>
      <OperatorSectionHeader
        title="1. 故事大纲（Story Seed）"
        subtitle="轻量初始条件；商业节奏、可拍性和连续性在下游检查"
        action={
          <div className="flex items-center gap-2">
            <StatusPill tone={status === "confirmed" ? "green" : "gray"}>
              {status === "confirmed" ? "已确认" : "草稿"}
            </StatusPill>
            <button
              type="button"
              disabled={controlsLocked}
              onClick={toggleEditing}
              className={operatorButtonClass("secondary")}
            >
              {editing
                ? "取消编辑"
                : status === "confirmed"
                ? "解冻为新草稿"
                : "编辑大纲"}
            </button>
          </div>
        }
      />
      <div className="space-y-5 p-5">
        <StorySeedBaselineEvidence story={story} />
        {notice ? (
          <p className="text-xs text-gray-600" role="status">
            {notice}
          </p>
        ) : null}
        {locked ? (
          <p className="text-xs text-amber-700">
            正文任务运行期间大纲已冻结；请先取消任务并等待状态确认。
          </p>
        ) : null}
        <StorySeedPlanningStatus
          taskId={planning.taskId}
          taskStatus={planning.taskStatus}
          active={planning.active}
          requesting={planning.requesting}
          progress={planning.progress}
          error={planning.error}
          onCancel={() => void planning.cancel()}
        />
        {editing && seed.schema === "story_seed_v1" ? (
          <StorySeedEditor seed={seed} onChange={setSeed} />
        ) : (
          <StorySeedView seed={seed} />
        )}
        {structured ? (
          <StoryStructuredOutlineEditor
            outline={structured}
            disabled={!editing || controlsLocked}
            onChange={(structured_outline) => {
              if (seed.schema === "story_seed_v2") {
                setSeed({ ...seed, structured_outline });
              }
            }}
          />
        ) : null}
        {showPlanning ? (
          <>
            <StorySeedPlanningInputs
              chapterCount={planningChapterCount}
              model={planningModel}
              disabled={planningDisabled}
              onChapterCount={setPlanningChapterCount}
              onModel={setPlanningModel}
            />
            <StorySeedPlanningAction
              hasStructuredOutline={Boolean(structured)}
              error={planningInputError}
              disabled={planningDisabled}
              onStart={startPlanning}
            />
          </>
        ) : null}
        {editing ? (
          <StorySeedSaveActions
            saving={saving}
            disabled={controlsLocked}
            canConfirm={Boolean(structured) && !validation}
            onSave={save}
          />
        ) : null}
      </div>
    </OperatorPanel>
  );
}
