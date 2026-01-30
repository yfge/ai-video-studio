"use client";

import { useEffect, useMemo, useState } from "react";
import type { Story } from "@/utils/api";
import { AIModelType, taskAPI } from "@/utils/api";
import { MultiModelSelector } from "@/components/shared";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import {
  downloadStoryNovel,
  generateStoryZhihuNovelAsync,
  type StoryNovelExportRequest,
} from "@/utils/storyNovelApi";

import { StoryNovelPreviewButton } from "./StoryNovelPreviewButton";
import { StoryNovelExportsHistory } from "./StoryNovelExportsHistory";

interface StoryNovelExportSectionProps {
  story: Story;
}

export function StoryNovelExportSection({
  story,
}: StoryNovelExportSectionProps) {
  const { showAlert } = useAlertModal();

  const [targetWords, setTargetWords] = useState(20000);
  const [chapterCount, setChapterCount] = useState<number | "">("");
  const [model, setModel] = useState<string>("");
  const [temperature, setTemperature] = useState<number>(0.7);

  const [taskId, setTaskId] = useState<number | null>(null);
  const [taskStatus, setTaskStatus] = useState<string | null>(null);
  const [progressDetail, setProgressDetail] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const canDownload = useMemo(
    () => Boolean(taskId && taskStatus === "completed"),
    [taskId, taskStatus],
  );
  const historyRefreshKey = useMemo(
    () => (taskStatus === "completed" ? taskId : null),
    [taskId, taskStatus],
  );

  const startExport = async () => {
    if (!story.business_id) {
      showAlert({
        message: "缺少故事 business_id，无法导出",
        variant: "error",
      });
      return;
    }
    try {
      setSubmitting(true);
      const payload: StoryNovelExportRequest = {
        style: "zhihu",
        target_words: targetWords,
        chapter_count: chapterCount === "" ? undefined : Number(chapterCount),
        model: model || undefined,
        temperature,
      };
      const res = await generateStoryZhihuNovelAsync(
        story.business_id,
        payload,
      );
      if (res.success && res.data?.task_id) {
        setTaskId(res.data.task_id);
        setTaskStatus(res.data.status);
        setProgressDetail("已创建任务，等待生成…");
        showAlert({
          message: `已创建导出任务（ID: ${res.data.task_id}），可在本页查看进度或前往任务页`,
          variant: "info",
        });
      } else {
        showAlert({
          message: `创建导出任务失败：${res.error || "未知错误"}`,
          variant: "error",
        });
      }
    } catch (e) {
      showAlert({
        message: e instanceof Error ? e.message : "创建导出任务失败",
        variant: "error",
      });
    } finally {
      setSubmitting(false);
    }
  };

  useEffect(() => {
    if (!taskId) return;

    let stopped = false;
    let timer: number | null = null;

    const load = async () => {
      const res = await taskAPI.getTask(String(taskId));
      if (!res.success || !res.data || stopped) return;
      setTaskStatus(res.data.status ?? null);
      setProgressDetail(res.data.progress_detail ?? null);
      if (res.data.status === "completed" || res.data.status === "failed") {
        stopped = true;
        if (timer) window.clearInterval(timer);
      }
    };

    void load();
    timer = window.setInterval(load, 5000);
    return () => {
      stopped = true;
      if (timer) window.clearInterval(timer);
    };
  }, [taskId]);

  const handleDownload = async () => {
    if (!taskId) return;
    try {
      setDownloading(true);
      const { blob, filename } = await downloadStoryNovel(taskId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename || `zhihu_novel_${story.title || "story"}.txt`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      showAlert({
        message: e instanceof Error ? e.message : "下载失败",
        variant: "error",
      });
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h2 className="text-xl font-semibold mb-3">导出知乎体小说</h2>
      <p className="text-sm text-gray-600 mb-4">
        将当前故事概要扩写为约 1–3
        万字的知乎体长文（异步任务生成，可在任务页查看）。
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            目标字数（10000 - 30000）
          </label>
          <input
            type="number"
            min={10000}
            max={30000}
            value={targetWords}
            onChange={(e) => setTargetWords(Number(e.target.value) || 20000)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            章节数（可选）
          </label>
          <input
            type="number"
            min={3}
            max={24}
            value={chapterCount}
            onChange={(e) =>
              setChapterCount(e.target.value ? Number(e.target.value) : "")
            }
            placeholder="留空自动估算"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <div className="text-xs text-gray-500 mt-1">
            建议每章约 1500–2200 字。
          </div>
        </div>

        <MultiModelSelector
          label="选择模型（可选）"
          value={model ? [model] : []}
          onChange={(ids) => setModel(ids[0] || "")}
          modelType={AIModelType.Text}
          multiple={false}
          helperText="为空将由后端自动选择"
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            温度（0.0 - 1.5）
          </label>
          <input
            type="range"
            min="0"
            max="1.5"
            step="0.1"
            value={temperature}
            onChange={(e) => setTemperature(parseFloat(e.target.value))}
            className="w-full"
          />
          <div className="text-sm text-gray-600">
            当前温度：{temperature.toFixed(1)}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3 mt-5">
        <button
          type="button"
          onClick={startExport}
          disabled={submitting}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
        >
          {submitting ? "创建中…" : "创建导出任务"}
        </button>
        {taskId && (
          <div className="text-sm text-gray-700">
            任务 ID：{taskId}，状态：{taskStatus || "unknown"}
          </div>
        )}
        {canDownload && (
          <StoryNovelPreviewButton taskId={taskId!} storyTitle={story.title} />
        )}
        {canDownload && (
          <button
            type="button"
            onClick={handleDownload}
            disabled={downloading}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            {downloading ? "下载中…" : "下载 .txt"}
          </button>
        )}
      </div>

      {progressDetail && (
        <div className="mt-4 text-sm text-gray-700 whitespace-pre-wrap">
          {progressDetail}
        </div>
      )}

      {story.business_id ? (
        <StoryNovelExportsHistory
          storyBusinessId={story.business_id}
          storyTitle={story.title}
          refreshKey={historyRefreshKey}
        />
      ) : null}
    </div>
  );
}
