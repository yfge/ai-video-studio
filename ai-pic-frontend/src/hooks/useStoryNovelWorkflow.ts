"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  acceptStoryNovelContinuityIssue,
  applyStoryNovelAdaptationPlan,
  approveStoryNovelAdaptationPlan,
  approveStoryNovelRevision,
  checkStoryNovelContinuity,
  cloneStoryNovelRevision,
  createStoryNovelRevision,
  generateStoryNovelRevisionAsync,
  generateStoryNovelAdaptationPlan,
  listStoryNovelRevisions,
  regenerateStoryNovelChapter,
  reorderStoryNovelChapters,
  resumeStoryNovelRevision,
  saveStoryNovelAdaptationPlan,
  saveStoryNovelChapter,
  updateStoryNovelCanon,
  updateStoryNovelLengthSpec,
} from "@/utils/api/endpoints";
import type {
  AdaptationPlanEpisode,
  Story,
  StoryNovelCanon,
  StoryNovelChapter,
  StoryNovelCreateRevisionPayload,
  StoryNovelRevision,
  StoryNovelUpdateLengthSpecPayload,
} from "@/utils/api/types";
import { useStoryNovelTaskTracking } from "./useStoryNovelTaskTracking";

export function useStoryNovelWorkflow(
  story: Story,
  onEpisodesApplied: () => Promise<void>,
) {
  const [revisions, setRevisions] = useState<StoryNovelRevision[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [canonicalId, setCanonicalId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const response = await listStoryNovelRevisions(story.business_id);
    if (!response.success || !response.data) {
      setError(response.error || "加载小说版本失败");
      return;
    }
    setRevisions(response.data.items);
    setCanonicalId(response.data.canonical_business_id || null);
    setSelectedId((value) =>
      value && response.data?.items.some((item) => item.business_id === value)
        ? value
        : response.data?.items[0]?.business_id || null,
    );
  }, [story.business_id]);

  useEffect(() => {
    void load();
  }, [load]);

  const task = useStoryNovelTaskTracking(load, setSelectedId);
  const { taskId, trackTask } = task;

  const current = useMemo(
    () => revisions.find((item) => item.business_id === selectedId) || null,
    [revisions, selectedId],
  );
  useEffect(() => {
    if (
      current &&
      (task.revisionId !== current.business_id || (!taskId && current.task_id))
    ) {
      trackTask(current.task_id || null, current.business_id);
    }
  }, [current, task.revisionId, taskId, trackTask]);
  const taskIsCurrent = task.revisionId === current?.business_id;
  const replaceRevision = (revision: StoryNovelRevision) => {
    setRevisions((items) => [
      revision,
      ...items.filter((item) => item.business_id !== revision.business_id),
    ]);
    setSelectedId(revision.business_id);
  };
  const mutate = async (
    request: Promise<{
      success: boolean;
      data?: StoryNovelRevision;
      error?: string;
    }>,
  ) => {
    setBusy(true);
    setError(null);
    const response = await request;
    setBusy(false);
    if (!response.success || !response.data) {
      setError(response.error || "操作失败");
      return false;
    }
    replaceRevision(response.data);
    return true;
  };
  const saveChapterAction = async (
    chapter: StoryNovelChapter,
    patch: Partial<StoryNovelChapter>,
  ) => {
    if (!current) return false;
    setBusy(true);
    setError(null);
    const response = await saveStoryNovelChapter(
      current.business_id,
      chapter.business_id,
      {
        title: patch.title,
        content_text: patch.content_text,
        summary: patch.summary,
        cliffhanger: patch.cliffhanger,
        expected_updated_at: chapter.updated_at,
      },
    );
    setBusy(false);
    if (!response.success || !response.data) {
      setError(response.error || "保存章节失败");
      return false;
    }
    replaceRevision({
      ...current,
      chapters: current.chapters.map((item) =>
        item.business_id === chapter.business_id ? response.data! : item,
      ),
    });
    await load();
    return true;
  };

  const saveCanonAction = async (canon: StoryNovelCanon) => {
    if (
      !current?.generation_plan?.version ||
      !current.generation_plan.canon_hash
    ) {
      return false;
    }
    setBusy(true);
    setError(null);
    const response = await updateStoryNovelCanon(current.business_id, {
      expected_plan_version: current.generation_plan.version,
      expected_canon_hash: current.generation_plan.canon_hash,
      canon,
    });
    setBusy(false);
    if (!response.success || !response.data) {
      setError(response.error || "保存 Canon 失败");
      return false;
    }
    replaceRevision(response.data.revision);
    return true;
  };

  return {
    revisions,
    current,
    selectedId,
    canonicalId,
    setSelectedId,
    taskId: taskIsCurrent ? task.taskId : null,
    taskStatus: taskIsCurrent ? task.taskStatus : null,
    progress: taskIsCurrent ? task.progress : null,
    busy: busy || task.busy,
    error: error || (taskIsCurrent ? task.error : null),
    activeTask: taskIsCurrent && task.active,
    createRevision: (payload: StoryNovelCreateRevisionPayload) =>
      mutate(createStoryNovelRevision(story.business_id, payload)),
    updateLengthSpec: (
      revisionId: string,
      payload: StoryNovelUpdateLengthSpecPayload,
    ) => mutate(updateStoryNovelLengthSpec(revisionId, payload)),
    startGeneration: () =>
      current &&
      task.startTask(
        generateStoryNovelRevisionAsync(current.business_id),
        current.business_id,
      ),
    cancelTask: task.cancelTask,
    resume: () =>
      current &&
      task.startTask(
        resumeStoryNovelRevision(current.business_id),
        current.business_id,
      ),
    regenerate: (chapter: StoryNovelChapter) =>
      current &&
      task.startTask(
        regenerateStoryNovelChapter(current.business_id, chapter.business_id),
        current.business_id,
      ),
    continuity: (reviewModel?: string) =>
      current &&
      task.startTask(
        checkStoryNovelContinuity(current.business_id, reviewModel),
        current.business_id,
      ),
    generatePlan: () =>
      current &&
      task.startTask(
        generateStoryNovelAdaptationPlan(current.business_id),
        current.business_id,
      ),
    saveChapter: saveChapterAction,
    saveCanon: saveCanonAction,
    reorder: (orderedIds: string[]) =>
      current?.updated_at
        ? mutate(
            reorderStoryNovelChapters(
              current.business_id,
              orderedIds,
              current.updated_at,
            ),
          )
        : Promise.resolve(false),
    clone: () =>
      current && mutate(cloneStoryNovelRevision(current.business_id)),
    approve: () =>
      current && mutate(approveStoryNovelRevision(current.business_id)),
    acceptIssue: (issueId: string, reason: string) =>
      current &&
      mutate(
        acceptStoryNovelContinuityIssue(current.business_id, issueId, reason),
      ),
    savePlan: (version: number, episodes: AdaptationPlanEpisode[]) =>
      current &&
      mutate(
        saveStoryNovelAdaptationPlan(current.business_id, version, episodes),
      ),
    approvePlan: (version: number) =>
      current &&
      mutate(approveStoryNovelAdaptationPlan(current.business_id, version)),
    applyPlan: async () => {
      if (!current) return false;
      setBusy(true);
      const response = await applyStoryNovelAdaptationPlan(current.business_id);
      setBusy(false);
      if (!response.success) {
        setError(response.error || "创建剧集失败");
        return false;
      }
      await Promise.all([load(), onEpisodesApplied()]);
      return true;
    },
  };
}
