"use client";

import { useEffect } from "react";
import {
  OperatorPanel,
  OperatorSectionHeader,
  StatusPill,
  operatorButtonClass,
  operatorInputClass,
} from "@/components/shared";
import { useStoryNovelWorkflow } from "@/hooks/useStoryNovelWorkflow";
import type { Story } from "@/utils/api/types";
import { StoryNovelAdaptationPanel } from "./StoryNovelAdaptationPanel";
import { StoryNovelCanonPanel } from "./StoryNovelCanonPanel";
import { StoryNovelChapterEditor } from "./StoryNovelChapterEditor";
import {
  StoryNovelGenerationStatus,
  storyNovelResumeLabel,
} from "./StoryNovelGenerationStatus";
import { StoryNovelLengthPanel } from "./StoryNovelLengthPanel";
import { StoryNovelQualityPanel } from "./StoryNovelQualityPanel";
import { StoryNovelReviewControls } from "./StoryNovelReviewControls";
import { StoryNovelV5ConsistencyPanel } from "./StoryNovelV5ConsistencyPanel";

export function StoryNovelWorkflowPanel({
  story,
  onEpisodesApplied,
  onTaskLockChange,
}: {
  story: Story;
  onEpisodesApplied: () => Promise<void>;
  onTaskLockChange?: (locked: boolean) => void;
}) {
  const workflow = useStoryNovelWorkflow(story, onEpisodesApplied);
  const current = workflow.current;
  useEffect(() => {
    onTaskLockChange?.(workflow.activeTask);
  }, [onTaskLockChange, workflow.activeTask]);
  const acceptIssue = (issueId: string) => {
    const reason = window.prompt("填写接受该阻断项的理由");
    if (reason?.trim()) void workflow.acceptIssue(issueId, reason.trim());
  };
  return (
    <>
      {story.story_seed_status === "confirmed" &&
      story.story_seed?.schema === "story_seed_v2" ? (
        <StoryNovelLengthPanel
          story={story}
          revision={current}
          locked={workflow.activeTask}
          busy={workflow.busy}
          onCreate={workflow.createRevision}
          onUpdate={workflow.updateLengthSpec}
        />
      ) : null}
      <OperatorPanel id="novel-workflow" className="scroll-mt-24">
        <OperatorSectionHeader
          title="3. 小说版本与正文生成"
          subtitle="审批后的小说是新系列叙事母本；保存与模型检查分离，不会自动产生费用"
        />
        <div className="grid gap-3 p-5">
          <label className="text-xs text-gray-600">
            当前版本
            <select
              aria-label="当前小说版本"
              value={workflow.selectedId || ""}
              disabled={workflow.activeTask}
              onChange={(event) => workflow.setSelectedId(event.target.value)}
              className={operatorInputClass("mt-1 w-full")}
            >
              <option value="">尚无版本</option>
              {workflow.revisions.map((revision) => (
                <option key={revision.business_id} value={revision.business_id}>
                  v{revision.revision_number} · {revision.lifecycle_status}
                  {revision.generation_plan?.length_profile
                    ? ` · ${
                        revision.generation_plan.length_profile.profile_name ||
                        revision.generation_plan.length_profile.profile_id
                      }`
                    : ""}
                  {revision.business_id === workflow.canonicalId
                    ? " · canonical"
                    : ""}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="flex flex-wrap items-center gap-2 border-t border-gray-100 px-5 py-4">
          {current?.lifecycle_status === "draft" && !current.chapters.length ? (
            <button
              type="button"
              disabled={
                workflow.busy ||
                workflow.activeTask ||
                (current.generation_plan?.schema ===
                  "story_novel_generation_plan.v5" &&
                  current.generation_plan?.schema_compile_status ===
                    "failed") ||
                !["ready", "failed", "planning"].includes(
                  current.generation_plan?.status || "",
                )
              }
              onClick={() => void workflow.startGeneration()}
              className={operatorButtonClass("primary")}
            >
              {current.generation_plan?.schema ===
                "story_novel_generation_plan.v5" &&
              current.generation_plan?.schema_compile_status === "failed"
                ? "Schema 编译失败（需新建 Revision）"
                : current.generation_plan?.status === "failed"
                ? "重试规划并生成正文"
                : current.generation_plan?.status === "planning"
                ? "继续规划并生成正文"
                : "开始生成正文"}
            </button>
          ) : null}
          {story.story_seed_status !== "confirmed" ? (
            <span className="text-xs text-amber-700">
              请先确认 Story Seed；确认不会自动调用小说生成。
            </span>
          ) : null}
          {current?.lifecycle_status === "draft" && current.chapters.length ? (
            <button
              type="button"
              disabled={workflow.busy || workflow.activeTask}
              onClick={() => void workflow.resume()}
              className={operatorButtonClass("secondary")}
            >
              {storyNovelResumeLabel(current.continuity_ledger)}
            </button>
          ) : null}
          {current ? (
            <>
              <StatusPill
                tone={
                  current.lifecycle_status === "approved" ? "green" : "blue"
                }
              >
                {current.lifecycle_status}
              </StatusPill>
              <StatusPill
                tone={
                  current.continuity_status === "passed" ? "green" : "amber"
                }
              >
                连续性 {current.continuity_status}
              </StatusPill>
              <StoryNovelGenerationStatus revision={current} />
            </>
          ) : null}
          {workflow.taskId ? (
            <>
              <StatusPill
                tone={workflow.taskStatus === "completed" ? "green" : "blue"}
              >
                任务 #{workflow.taskId} · {workflow.taskStatus}
              </StatusPill>
              {workflow.activeTask ? (
                <button
                  type="button"
                  disabled={workflow.busy}
                  onClick={() => void workflow.cancelTask()}
                  className={operatorButtonClass("secondary")}
                >
                  取消正文任务
                </button>
              ) : null}
            </>
          ) : null}
        </div>
        {current?.lifecycle_status === "draft" ? (
          <div className="flex flex-wrap gap-2 border-t border-gray-100 px-5 py-4">
            <StoryNovelReviewControls
              disabled={
                workflow.busy || workflow.activeTask || !current.chapters.length
              }
              onRun={(model) => void workflow.continuity(model)}
            />
            <button
              type="button"
              disabled={
                workflow.busy ||
                workflow.activeTask ||
                current.continuity_status !== "passed"
              }
              onClick={() => void workflow.approve()}
              className={operatorButtonClass("primary")}
            >
              审批为 canonical
            </button>
          </div>
        ) : current ? (
          <div className="border-t border-gray-100 px-5 py-4">
            <button
              type="button"
              disabled={workflow.busy || workflow.activeTask}
              onClick={() => void workflow.clone()}
              className={operatorButtonClass("secondary")}
            >
              复制为新草稿
            </button>
          </div>
        ) : null}
        {workflow.progress ? (
          <p className="px-5 pb-3 text-xs text-gray-500">{workflow.progress}</p>
        ) : null}
        {workflow.error ? (
          <p role="alert" className="px-5 pb-3 text-xs text-red-600">
            {workflow.error}
          </p>
        ) : null}
      </OperatorPanel>
      <StoryNovelV5ConsistencyPanel revision={current} />
      {current?.lifecycle_status === "draft" &&
      current.generation_plan?.canon ? (
        <StoryNovelCanonPanel
          revision={current}
          busy={workflow.busy || workflow.activeTask}
          onSave={workflow.saveCanon}
        />
      ) : null}
      {current?.continuity_report ? (
        <StoryNovelQualityPanel
          report={current.continuity_report}
          onAcceptIssue={acceptIssue}
        />
      ) : null}
      {current?.chapters.length ? (
        <StoryNovelChapterEditor
          storyId={story.business_id}
          revision={current}
          busy={workflow.busy || workflow.activeTask}
          onSave={(chapter, patch) => void workflow.saveChapter(chapter, patch)}
          onMove={(ids) => void workflow.reorder(ids)}
          onRegenerate={(chapter) => void workflow.regenerate(chapter)}
        />
      ) : null}
      {current ? (
        <StoryNovelAdaptationPanel
          revision={current}
          busy={workflow.busy || workflow.activeTask}
          onGenerate={() => void workflow.generatePlan()}
          onSave={(version, rows) => void workflow.savePlan(version, rows)}
          onApprove={(version) => void workflow.approvePlan(version)}
          onApply={() => void workflow.applyPlan()}
        />
      ) : null}
    </>
  );
}
