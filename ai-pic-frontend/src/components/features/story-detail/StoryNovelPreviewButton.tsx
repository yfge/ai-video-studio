"use client";

import { useMemo, useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import { fetchStoryNovelText } from "@/utils/storyNovelApi";

interface StoryNovelPreviewButtonProps {
  taskId: number;
  storyTitle?: string;
}

export function StoryNovelPreviewButton({
  taskId,
  storyTitle,
}: StoryNovelPreviewButtonProps) {
  const { showAlert } = useAlertModal();

  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [text, setText] = useState<string>("");
  const [filename, setFilename] = useState<string | null>(null);

  const title = useMemo(() => {
    if (filename) return filename;
    if (storyTitle) return `知乎体小说 - ${storyTitle}`;
    return "知乎体小说";
  }, [filename, storyTitle]);

  const loadText = async (force = false) => {
    if (!taskId) return;
    if (!force && text) return;
    try {
      setLoading(true);
      const res = await fetchStoryNovelText(taskId);
      setText(res.text || "");
      setFilename(res.filename);
    } catch (e) {
      showAlert({
        message: e instanceof Error ? e.message : "获取内容失败",
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleOpen = async () => {
    setOpen(true);
    await loadText(false);
  };

  const handleCopy = async () => {
    if (!text) {
      await loadText(true);
    }
    if (!text) {
      showAlert({ message: "内容为空，无法复制", variant: "error" });
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      showAlert({ message: "已复制全文到剪贴板", variant: "success" });
    } catch (e) {
      showAlert({
        message: e instanceof Error ? e.message : "复制失败",
        variant: "error",
      });
    }
  };

  return (
    <>
      <button
        type="button"
        onClick={handleOpen}
        className="bg-slate-600 text-white px-4 py-2 rounded-lg hover:bg-slate-700 disabled:opacity-50"
      >
        预览全文
      </button>

      <Modal
        isOpen={open}
        onClose={() => setOpen(false)}
        title={title}
        maxWidth="max-w-4xl"
        footer={
          <>
            <button
              type="button"
              onClick={() => void loadText(true)}
              disabled={loading}
              className="px-4 py-2 rounded-lg border border-gray-300 bg-white hover:bg-gray-50 disabled:opacity-50"
            >
              {loading ? "刷新中…" : "刷新"}
            </button>
            <button
              type="button"
              onClick={() => void handleCopy()}
              disabled={loading}
              className="px-4 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              复制全文
            </button>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="px-4 py-2 rounded-lg border border-gray-300 bg-white hover:bg-gray-50"
            >
              关闭
            </button>
          </>
        }
      >
        {loading && !text ? (
          <div className="text-sm text-gray-600">加载中…</div>
        ) : (
          <div className="whitespace-pre-wrap text-sm leading-relaxed text-gray-900">
            {text || "暂无内容"}
          </div>
        )}
      </Modal>
    </>
  );
}
