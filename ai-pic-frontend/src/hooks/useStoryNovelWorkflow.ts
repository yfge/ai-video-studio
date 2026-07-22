"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  acceptStoryNovelContinuityIssue,
  applyStoryNovelAdaptationPlan,
  approveStoryNovelAdaptationPlan,
  approveStoryNovelRevision,
  checkStoryNovelContinuity,
  cloneStoryNovelRevision,
  generateStoryNovelAdaptationPlan,
  generateStoryZhihuNovelAsync,
  listStoryNovelRevisions,
  regenerateStoryNovelChapter,
  reorderStoryNovelChapters,
  resumeStoryNovelRevision,
  saveStoryNovelAdaptationPlan,
  saveStoryNovelChapter,
  taskAPI,
} from "@/utils/api/endpoints";
import type {
  AdaptationPlanEpisode,
  Story,
  StoryNovelChapter,
  StoryNovelRevision,
} from "@/utils/api/types";

const TERMINAL = new Set(["completed", "failed", "cancelled"]);

export function useStoryNovelWorkflow(
  story: Story,
  onEpisodesApplied: () => Promise<void>,
) {
  const [revisions, setRevisions] = useState<StoryNovelRevision[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [canonicalId, setCanonicalId] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<number | null>(null);
  const [taskStatus, setTaskStatus] = useState<string | null>(null);
  const [progress, setProgress] = useState<string | null>(null);
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

  useEffect(() => {
    if (!taskId || (taskStatus && TERMINAL.has(taskStatus))) return;
    let active = true;
    const refresh = async () => {
      const response = await taskAPI.getTask(String(taskId));
      if (!active || !response.success || !response.data) return;
      setTaskStatus(response.data.status);
      setProgress(
        response.data.progress_detail || response.data.description || null,
      );
      if (response.data.status === "failed") {
        setError(response.data.error_message || "小说任务失败");
      }
      if (response.data.status === "completed") await load();
    };
    void refresh();
    const timer = window.setInterval(refresh, 3000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [load, taskId, taskStatus]);

  const current = useMemo(
    () => revisions.find((item) => item.business_id === selectedId) || null,
    [revisions, selectedId],
  );

  const startTask = async (
    request: Promise<{
      success: boolean;
      data?: {
        task_id: number;
        status: string;
        revision_business_id?: string | null;
      };
      error?: string;
    }>,
  ) => {
    setBusy(true);
    setError(null);
    const response = await request;
    setBusy(false);
    if (!response.success || !response.data) {
      setError(response.error || "创建任务失败");
      return;
    }
    setTaskId(response.data.task_id);
    setTaskStatus(response.data.status);
    setProgress("任务已创建，等待处理…");
    if (response.data.revision_business_id) {
      setSelectedId(response.data.revision_business_id);
    }
    await load();
  };

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

  return {
    revisions,
    current,
    selectedId,
    canonicalId,
    setSelectedId,
    taskId,
    taskStatus,
    progress,
    busy,
    error,
    generate: (targetWords: number, chapterCount?: number) =>
      startTask(
        generateStoryZhihuNovelAsync(story.business_id, {
          style: "prose",
          target_words: targetWords,
          chapter_count: chapterCount,
        }),
      ),
    resume: () =>
      current && startTask(resumeStoryNovelRevision(current.business_id)),
    regenerate: (chapter: StoryNovelChapter) =>
      current &&
      startTask(
        regenerateStoryNovelChapter(current.business_id, chapter.business_id),
      ),
    continuity: () =>
      current && startTask(checkStoryNovelContinuity(current.business_id)),
    generatePlan: () =>
      current &&
      startTask(generateStoryNovelAdaptationPlan(current.business_id)),
    saveChapter: saveChapterAction,
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
