"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import {
  downloadStoryNovel,
  listStoryNovelExports,
  type StoryNovelExportSummary,
} from "@/utils/storyNovelApi";

import { StoryNovelPreviewButton } from "./StoryNovelPreviewButton";

interface StoryNovelExportsHistoryProps {
  storyBusinessId: string;
  storyTitle?: string;
  refreshKey?: number | string | null;
}

const formatDateTime = (value: string | null | undefined): string => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
};

export function StoryNovelExportsHistory({
  storyBusinessId,
  storyTitle,
  refreshKey,
}: StoryNovelExportsHistoryProps) {
  const { showAlert } = useAlertModal();

  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState<StoryNovelExportSummary[]>([]);
  const [downloadingTaskId, setDownloadingTaskId] = useState<number | null>(
    null,
  );

  const latest = useMemo(() => items[0] ?? null, [items]);

  const load = useCallback(async () => {
    if (!storyBusinessId) return;
    try {
      setLoading(true);
      const res = await listStoryNovelExports(storyBusinessId, 20);
      if (res.success && res.data) {
        setItems(res.data.items || []);
        return;
      }
      showAlert({
        message: `获取导出历史失败：${res.error || "未知错误"}`,
        variant: "error",
      });
    } catch (e) {
      showAlert({
        message: e instanceof Error ? e.message : "获取导出历史失败",
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  }, [showAlert, storyBusinessId]);

  useEffect(() => {
    void load();
  }, [load, refreshKey]);

  const handleDownload = async (taskId: number) => {
    try {
      setDownloadingTaskId(taskId);
      const { blob, filename } = await downloadStoryNovel(taskId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename || `zhihu_novel_${storyTitle || "story"}.txt`;
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
      setDownloadingTaskId(null);
    }
  };

  return (
    <div className="mt-6 border-t border-gray-200 pt-5">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-base font-semibold text-gray-900">历史导出</h3>
        <button
          type="button"
          onClick={() => void load()}
          disabled={loading}
          className="px-3 py-1.5 rounded-md border border-gray-300 bg-white text-sm hover:bg-gray-50 disabled:opacity-50"
        >
          {loading ? "刷新中…" : "刷新列表"}
        </button>
      </div>

      {!latest ? (
        <div className="mt-3 text-sm text-gray-500">暂无导出记录</div>
      ) : (
        <div className="mt-3 space-y-2">
          {items.slice(0, 5).map((item) => {
            const words = item.total_words || item.target_words;
            const chapter = item.chapter_count
              ? `${item.chapter_count} 章`
              : "";
            const meta = [
              words ? `约 ${words} 字` : "",
              chapter,
              item.created_at ? formatDateTime(item.created_at) : "",
            ]
              .filter(Boolean)
              .join(" · ");

            return (
              <div
                key={item.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-md bg-gray-50 px-3 py-2"
              >
                <div className="text-sm text-gray-700">
                  <span className="font-medium">
                    任务 {item.task_id ?? "—"}
                  </span>
                  {meta ? (
                    <span className="text-gray-500 ml-2">{meta}</span>
                  ) : null}
                </div>

                {item.task_id ? (
                  <div className="flex items-center gap-2">
                    <StoryNovelPreviewButton
                      taskId={item.task_id}
                      storyTitle={storyTitle}
                    />
                    <button
                      type="button"
                      onClick={() => void handleDownload(item.task_id!)}
                      disabled={downloadingTaskId === item.task_id}
                      className="bg-green-600 text-white px-3 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
                    >
                      {downloadingTaskId === item.task_id
                        ? "下载中…"
                        : "下载 .txt"}
                    </button>
                  </div>
                ) : (
                  <div className="text-xs text-gray-500">无 task_id</div>
                )}
              </div>
            );
          })}

          {items.length > 5 ? (
            <div className="text-xs text-gray-500">仅显示最近 5 条</div>
          ) : null}
        </div>
      )}
    </div>
  );
}
