"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { scriptAPI } from "@/utils/api";
import type { Script, StoryboardFrame, StoryboardPayload } from "@/utils/api";

interface WorkspaceStoryboardTabContentProps {
  episodeKey: string;
  scripts: Script[];
  selectedScriptId: number | null;
  selectedScript: Script | null;
  onSelectScript: (id: number | null) => void;
  hasStoryboard: boolean;
  showAlert: (options: { message: string; variant: "info" | "success" | "warning" | "error" }) => void;
}

// Note: selectedScript and onSelectScript are included for future script selector feature

const formatMs = (ms: number): string => {
  const safe = Math.max(0, Math.trunc(ms));
  const totalSeconds = Math.floor(safe / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
};

export function WorkspaceStoryboardTabContent({
  episodeKey,
  scripts,
  selectedScriptId,
  selectedScript: _selectedScript,
  onSelectScript: _onSelectScript,
  hasStoryboard,
  showAlert,
}: WorkspaceStoryboardTabContentProps) {
  const router = useRouter();
  const [storyboard, setStoryboard] = useState<StoryboardPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatingImages, setGeneratingImages] = useState(false);
  const [selectedFrames, setSelectedFrames] = useState<Set<number>>(new Set());

  // Load storyboard when script changes
  useEffect(() => {
    if (!selectedScriptId) {
      setStoryboard(null);
      return;
    }
    let cancelled = false;
    const loadStoryboard = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await scriptAPI.getStoryboard(selectedScriptId);
        if (cancelled) return;
        if (res.success && res.data) {
          setStoryboard(res.data);
        } else {
          setStoryboard(null);
          if (res.error) setError(res.error);
        }
      } catch (err) {
        if (!cancelled) {
          console.error("Failed to load storyboard:", err);
          setError("加载分镜失败");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    loadStoryboard();
    return () => { cancelled = true; };
  }, [selectedScriptId]);

  const handleOpenFullEditor = useCallback(() => {
    const params = new URLSearchParams();
    if (selectedScriptId) {
      params.set("scriptId", String(selectedScriptId));
    }
    const suffix = params.toString();
    router.push(`/episodes/${episodeKey}/storyboard${suffix ? `?${suffix}` : ""}`);
  }, [router, episodeKey, selectedScriptId]);

  const handleToggleFrame = useCallback((index: number) => {
    setSelectedFrames((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  }, []);

  const handleSelectAll = useCallback(() => {
    if (!storyboard?.frames) return;
    setSelectedFrames(new Set(storyboard.frames.map((_, i) => i)));
  }, [storyboard?.frames]);

  const handleDeselectAll = useCallback(() => {
    setSelectedFrames(new Set());
  }, []);

  const handleGenerateImages = useCallback(async () => {
    if (!selectedScriptId || selectedFrames.size === 0) return;
    try {
      setGeneratingImages(true);
      const frameIndices = Array.from(selectedFrames);
      const res = await scriptAPI.generateStoryboardImages(selectedScriptId, {
        frames: frameIndices,
        count: 1,
      });
      if (res.success) {
        showAlert({ message: `已开始为 ${frameIndices.length} 个分镜帧生成图像`, variant: "info" });
        // Refresh storyboard after a delay
        setTimeout(async () => {
          const refreshRes = await scriptAPI.getStoryboard(selectedScriptId);
          if (refreshRes.success && refreshRes.data) {
            setStoryboard(refreshRes.data);
          }
        }, 2000);
      } else {
        showAlert({ message: `生成图像失败：${res.error || "未知错误"}`, variant: "error" });
      }
    } catch (err) {
      console.error("Failed to generate images:", err);
      showAlert({ message: "生成图像失败", variant: "error" });
    } finally {
      setGeneratingImages(false);
      setSelectedFrames(new Set());
    }
  }, [selectedScriptId, selectedFrames, showAlert]);

  if (scripts.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <h3 className="text-lg font-medium text-gray-900 mb-2">暂无剧本</h3>
        <p className="text-gray-500 mb-4">请先生成剧本和时间轴，然后才能管理分镜</p>
      </div>
    );
  }

  if (!hasStoryboard && !storyboard?.frames?.length) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <h3 className="text-lg font-medium text-gray-900 mb-2">暂无分镜帧</h3>
        <p className="text-gray-500 mb-4">请先在时间轴页生成分镜帧占位</p>
        <button
          onClick={handleOpenFullEditor}
          className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
        >
          前往分镜管理
        </button>
      </div>
    );
  }

  const frames = storyboard?.frames || [];
  const framesWithImages = frames.filter((f) => f.start_image_url || f.image_url);
  const framesWithoutImages = frames.filter((f) => !f.start_image_url && !f.image_url);

  return (
    <div className="space-y-4">
      {/* Header with stats and actions */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">分镜帧</h3>
            <p className="text-sm text-gray-500">
              共 {frames.length} 帧 · {framesWithImages.length} 帧有图像 · {framesWithoutImages.length} 帧待生成
            </p>
          </div>
          <div className="flex items-center gap-2">
            {selectedFrames.size > 0 && (
              <>
                <span className="text-sm text-gray-500">已选 {selectedFrames.size} 帧</span>
                <button
                  onClick={handleGenerateImages}
                  disabled={generatingImages}
                  className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
                >
                  {generatingImages ? "生成中..." : "生成图像"}
                </button>
                <button
                  onClick={handleDeselectAll}
                  className="text-gray-600 px-3 py-1.5 rounded text-sm hover:bg-gray-100"
                >
                  取消选择
                </button>
              </>
            )}
            {selectedFrames.size === 0 && framesWithoutImages.length > 0 && (
              <button
                onClick={handleSelectAll}
                className="text-blue-600 px-3 py-1.5 rounded text-sm hover:bg-blue-50"
              >
                选择全部
              </button>
            )}
            <button
              onClick={handleOpenFullEditor}
              className="text-purple-600 px-3 py-1.5 rounded text-sm hover:bg-purple-50"
            >
              打开完整编辑器 →
            </button>
          </div>
        </div>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-500">加载分镜中...</p>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="bg-red-50 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

      {/* Frame grid */}
      {!loading && frames.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {frames.map((frame, index) => (
            <FrameCard
              key={frame.frame_id || index}
              frame={frame}
              index={index}
              selected={selectedFrames.has(index)}
              onToggle={() => handleToggleFrame(index)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface FrameCardProps {
  frame: StoryboardFrame;
  index: number;
  selected: boolean;
  onToggle: () => void;
}

function FrameCard({ frame, index, selected, onToggle }: FrameCardProps) {
  const imageUrl = frame.start_image_url || frame.image_url;
  const hasImage = Boolean(imageUrl);
  const startMs = frame.start_ms ?? 0;
  const endMs = frame.end_ms ?? 0;

  return (
    <div
      className={`bg-white rounded-lg shadow overflow-hidden cursor-pointer transition-all ${
        selected ? "ring-2 ring-blue-500" : "hover:shadow-md"
      }`}
      onClick={onToggle}
    >
      {/* Image or placeholder */}
      <div className="aspect-video bg-gray-100 relative">
        {hasImage ? (
          <img
            src={imageUrl}
            alt={`Frame ${index + 1}`}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        )}
        {/* Selection indicator */}
        {selected && (
          <div className="absolute top-2 right-2 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        )}
        {/* Frame number */}
        <div className="absolute bottom-1 left-1 bg-black/60 text-white text-xs px-1.5 py-0.5 rounded">
          #{index + 1}
        </div>
        {/* Video indicator */}
        {frame.video_url && (
          <div className="absolute bottom-1 right-1 bg-purple-500/80 text-white text-xs px-1.5 py-0.5 rounded">
            视频
          </div>
        )}
      </div>
      {/* Frame info */}
      <div className="p-2">
        <div className="text-xs text-gray-500 truncate">
          {formatMs(startMs)} - {formatMs(endMs)}
        </div>
        {frame.description && (
          <p className="text-xs text-gray-700 mt-1 line-clamp-2">{frame.description}</p>
        )}
      </div>
    </div>
  );
}
