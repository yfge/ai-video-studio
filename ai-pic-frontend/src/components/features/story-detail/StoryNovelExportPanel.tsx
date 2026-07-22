"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  OperatorPanel,
  OperatorSectionHeader,
  StatusPill,
  operatorButtonClass,
  operatorInputClass,
} from "@/components/shared";
import {
  downloadStoryNovel,
  generateStoryZhihuNovelAsync,
  taskAPI,
} from "@/utils/api/endpoints";
import type { Story } from "@/utils/api/types";

const TERMINAL_STATUSES = new Set(["completed", "failed", "cancelled"]);

export function StoryNovelExportPanel({ story }: { story: Story }) {
  const [targetWords, setTargetWords] = useState(20000);
  const [chapterCount, setChapterCount] = useState<number | "">("");
  const [taskId, setTaskId] = useState<number | null>(null);
  const [taskStatus, setTaskStatus] = useState<string | null>(null);
  const [progress, setProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    if (!taskId || (taskStatus && TERMINAL_STATUSES.has(taskStatus))) return;
    let active = true;
    const refresh = async () => {
      const response = await taskAPI.getTask(String(taskId));
      if (!active || !response.success || !response.data) return;
      setTaskStatus(response.data.status);
      setProgress(
        response.data.progress_detail || response.data.description || null,
      );
      if (response.data.status === "failed") {
        setError(response.data.error_message || "小说生成失败");
      }
    };
    void refresh();
    const timer = window.setInterval(refresh, 5000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [taskId, taskStatus]);

  const startExport = async () => {
    if (!story.business_id) {
      setError("当前故事缺少业务 ID，无法生成小说");
      return;
    }
    setSubmitting(true);
    setError(null);
    const response = await generateStoryZhihuNovelAsync(story.business_id, {
      style: "zhihu",
      target_words: targetWords,
      chapter_count: chapterCount === "" ? undefined : chapterCount,
    });
    setSubmitting(false);
    if (!response.success || !response.data?.task_id) {
      setError(response.error || "创建小说生成任务失败");
      return;
    }
    setTaskId(response.data.task_id);
    setTaskStatus(response.data.status);
    setProgress("任务已创建，等待生成…");
  };

  const download = async () => {
    if (!taskId) return;
    try {
      setDownloading(true);
      setError(null);
      const { blob, filename } = await downloadStoryNovel(taskId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename || `novel-${story.title}.txt`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (downloadError) {
      setError(
        downloadError instanceof Error ? downloadError.message : "下载失败",
      );
    } finally {
      setDownloading(false);
    }
  };

  return (
    <OperatorPanel id="novel-export" className="scroll-mt-24">
      <OperatorSectionHeader
        title="故事导成小说"
        subtitle="将故事概要扩写为 1–3 万字的知乎体长文"
      />
      <div className="grid gap-4 p-5 md:grid-cols-2">
        <label className="text-xs font-medium text-gray-600">
          目标字数
          <input
            aria-label="目标字数"
            type="number"
            min={10000}
            max={30000}
            value={targetWords}
            onChange={(event) => setTargetWords(Number(event.target.value))}
            className={operatorInputClass("mt-1 w-full")}
          />
        </label>
        <label className="text-xs font-medium text-gray-600">
          章节数（可选）
          <input
            aria-label="章节数（可选）"
            type="number"
            min={3}
            max={24}
            value={chapterCount}
            placeholder="自动估算"
            onChange={(event) =>
              setChapterCount(
                event.target.value ? Number(event.target.value) : "",
              )
            }
            className={operatorInputClass("mt-1 w-full")}
          />
        </label>
      </div>
      <div className="flex flex-wrap items-center gap-3 border-t border-gray-100 px-5 py-4">
        <button
          type="button"
          onClick={() => void startExport()}
          disabled={submitting}
          className={operatorButtonClass("primary")}
        >
          {submitting ? "创建中…" : "生成小说"}
        </button>
        {taskId ? (
          <>
            <StatusPill tone={taskStatus === "completed" ? "green" : "blue"}>
              任务 #{taskId} · {taskStatus || "pending"}
            </StatusPill>
            <Link
              href={`/tasks?task_id=${taskId}`}
              className={operatorButtonClass("secondary")}
            >
              查看任务
            </Link>
          </>
        ) : null}
        {taskStatus === "completed" ? (
          <button
            type="button"
            onClick={() => void download()}
            disabled={downloading}
            className={operatorButtonClass("secondary")}
          >
            {downloading ? "下载中…" : "下载小说"}
          </button>
        ) : null}
      </div>
      {progress ? (
        <p className="px-5 pb-4 text-xs text-gray-500">{progress}</p>
      ) : null}
      {error ? (
        <p role="alert" className="px-5 pb-4 text-xs text-red-600">
          {error}
        </p>
      ) : null}
    </OperatorPanel>
  );
}
