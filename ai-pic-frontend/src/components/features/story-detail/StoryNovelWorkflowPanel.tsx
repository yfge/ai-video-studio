"use client";

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
import { StoryNovelChapterEditor } from "./StoryNovelChapterEditor";
import { StoryNovelGenerationStatus } from "./StoryNovelGenerationStatus";

export function StoryNovelWorkflowPanel({
  story,
  onEpisodesApplied,
}: {
  story: Story;
  onEpisodesApplied: () => Promise<void>;
}) {
  const workflow = useStoryNovelWorkflow(story, onEpisodesApplied);
  const current = workflow.current;
  const acceptIssue = (issueId: string) => {
    const reason = window.prompt("填写接受该阻断项的理由");
    if (reason?.trim()) void workflow.acceptIssue(issueId, reason.trim());
  };
  return (
    <>
      <OperatorPanel id="novel-workflow" className="scroll-mt-24">
        <OperatorSectionHeader
          title="2. 小说版本与章节编辑"
          subtitle="审批后的小说是新系列叙事母本；保存与模型检查分离，不会自动产生费用"
        />
        <div className="grid gap-3 p-5">
          <label className="text-xs text-gray-600">
            当前版本
            <select
              aria-label="当前小说版本"
              value={workflow.selectedId || ""}
              onChange={(event) => workflow.setSelectedId(event.target.value)}
              className={operatorInputClass("mt-1 w-full")}
            >
              <option value="">尚无版本</option>
              {workflow.revisions.map((revision) => (
                <option key={revision.business_id} value={revision.business_id}>
                  v{revision.revision_number} · {revision.lifecycle_status}
                  {revision.business_id === workflow.canonicalId
                    ? " · canonical"
                    : ""}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="flex flex-wrap items-center gap-2 border-t border-gray-100 px-5 py-4">
          <button
            type="button"
            disabled={workflow.busy || story.story_seed_status !== "confirmed"}
            onClick={() => void workflow.generate()}
            className={operatorButtonClass("primary")}
          >
            根据故事大纲生成长篇小说
          </button>
          {story.story_seed_status !== "confirmed" ? (
            <span className="text-xs text-amber-700">
              请先确认 Story Seed；确认不会自动调用小说生成。
            </span>
          ) : null}
          {current?.lifecycle_status === "draft" ? (
            <button
              type="button"
              disabled={workflow.busy}
              onClick={() => void workflow.resume()}
              className={operatorButtonClass("secondary")}
            >
              补齐缺失章节
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
            <StatusPill
              tone={workflow.taskStatus === "completed" ? "green" : "blue"}
            >
              任务 #{workflow.taskId} · {workflow.taskStatus}
            </StatusPill>
          ) : null}
        </div>
        {current?.lifecycle_status === "draft" ? (
          <div className="flex flex-wrap gap-2 border-t border-gray-100 px-5 py-4">
            <button
              type="button"
              disabled={workflow.busy || !current.chapters.length}
              onClick={() => void workflow.continuity()}
              className={operatorButtonClass("secondary")}
            >
              运行连续性检查
            </button>
            <button
              type="button"
              disabled={workflow.busy || current.continuity_status !== "passed"}
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
              disabled={workflow.busy}
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
        {current?.continuity_report?.issues?.length ? (
          <div className="border-t border-gray-100 p-5">
            <h3 className="text-sm font-semibold">连续性报告</h3>
            <div className="mt-3 space-y-2">
              {current.continuity_report.issues.map((issue) => (
                <div
                  key={issue.id}
                  className="rounded-md border border-gray-200 p-3 text-xs"
                >
                  <div className="flex items-center gap-2">
                    <StatusPill
                      tone={issue.severity === "blocking" ? "red" : "amber"}
                    >
                      {issue.severity}
                    </StatusPill>
                    <span>{issue.message}</span>
                  </div>
                  {issue.suggestion ? (
                    <p className="mt-2 text-gray-500">{issue.suggestion}</p>
                  ) : null}
                  {issue.severity === "blocking" && !issue.accepted_reason ? (
                    <button
                      type="button"
                      onClick={() => acceptIssue(issue.id)}
                      className={operatorButtonClass("secondary", "mt-2")}
                    >
                      填写接受理由
                    </button>
                  ) : null}
                  {issue.accepted_reason ? (
                    <p className="mt-2 text-green-700">
                      已接受：{issue.accepted_reason}
                    </p>
                  ) : null}
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </OperatorPanel>
      {current?.chapters.length ? (
        <StoryNovelChapterEditor
          storyId={story.business_id}
          revision={current}
          busy={workflow.busy}
          onSave={(chapter, patch) => void workflow.saveChapter(chapter, patch)}
          onMove={(ids) => void workflow.reorder(ids)}
          onRegenerate={(chapter) => void workflow.regenerate(chapter)}
        />
      ) : null}
      {current?.lifecycle_status === "approved" ? (
        <StoryNovelAdaptationPanel
          revision={current}
          busy={workflow.busy}
          onGenerate={() => void workflow.generatePlan()}
          onSave={(version, rows) => void workflow.savePlan(version, rows)}
          onApprove={(version) => void workflow.approvePlan(version)}
          onApply={() => void workflow.applyPlan()}
        />
      ) : null}
    </>
  );
}
