"use client";

import React from "react";

/**
 * 投流素材数据类型
 */
export interface AdSnippetData {
  asset_id?: string;
  duration_seconds?: number;
  hook_type?: string;
  source_episode?: number;
  source_timecode_start?: string;
  source_timecode_end?: string;
  key_line?: string;
  visual_hook?: string;
  shot_list?: string[];
  cliff_or_cta?: string;
  hook?: string; // 简化版本的 hook 字段
  visual_summary?: string;
  call_to_action?: string;
}

interface AdSnippetCardProps {
  /** 投流素材数据 */
  snippet: AdSnippetData;
  /** 是否为紧凑模式 */
  compact?: boolean;
  /** 点击回调 */
  onClick?: () => void;
  /** 额外的 className */
  className?: string;
}

/**
 * 时长对应的样式
 */
const DURATION_STYLES: Record<number, { bg: string; border: string }> = {
  15: {
    bg: "bg-blue-50 dark:bg-blue-900/20",
    border: "border-blue-200 dark:border-blue-800",
  },
  30: {
    bg: "bg-green-50 dark:bg-green-900/20",
    border: "border-green-200 dark:border-green-800",
  },
  60: {
    bg: "bg-purple-50 dark:bg-purple-900/20",
    border: "border-purple-200 dark:border-purple-800",
  },
};

/**
 * 投流素材卡片组件
 *
 * 显示 15/30/60 秒投流素材的关键信息
 */
export function AdSnippetCard({
  snippet,
  compact = false,
  onClick,
  className = "",
}: AdSnippetCardProps) {
  const duration = snippet.duration_seconds || 15;
  const style = DURATION_STYLES[duration] || DURATION_STYLES[15];

  if (compact) {
    return (
      <div
        className={`
          inline-flex items-center gap-1.5 px-2 py-1 rounded border text-xs
          ${style.bg} ${style.border}
          ${onClick ? "cursor-pointer hover:opacity-80" : ""}
          ${className}
        `}
        onClick={onClick}
        title={snippet.key_line || snippet.hook || "投流素材"}
      >
        <DurationBadge seconds={duration} />
        <span className="truncate max-w-[120px]">
          {snippet.key_line || snippet.hook || "素材"}
        </span>
      </div>
    );
  }

  return (
    <div
      className={`
        rounded-lg border p-3 space-y-2
        ${style.bg} ${style.border}
        ${onClick ? "cursor-pointer hover:shadow-md transition-shadow" : ""}
        ${className}
      `}
      onClick={onClick}
    >
      {/* 头部：时长 + 类型 */}
      <div className="flex items-center justify-between">
        <DurationBadge seconds={duration} />
        {snippet.hook_type && (
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {snippet.hook_type}
          </span>
        )}
      </div>

      {/* 核心钩子/台词 */}
      {(snippet.key_line || snippet.hook) && (
        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
          &ldquo;{snippet.key_line || snippet.hook}&rdquo;
        </div>
      )}

      {/* 视觉钩子 */}
      {(snippet.visual_hook || snippet.visual_summary) && (
        <div className="text-xs text-gray-600 dark:text-gray-400">
          <span className="font-medium">画面：</span>
          {snippet.visual_hook || snippet.visual_summary}
        </div>
      )}

      {/* 镜头列表 */}
      {snippet.shot_list && snippet.shot_list.length > 0 && (
        <div className="text-xs text-gray-500 dark:text-gray-500">
          <span className="font-medium">镜头：</span>
          {snippet.shot_list.slice(0, 3).join(" → ")}
          {snippet.shot_list.length > 3 && ` +${snippet.shot_list.length - 3}`}
        </div>
      )}

      {/* CTA */}
      {(snippet.cliff_or_cta || snippet.call_to_action) && (
        <div className="text-xs text-blue-600 dark:text-blue-400 font-medium">
          {snippet.cliff_or_cta || snippet.call_to_action}
        </div>
      )}

      {/* 时间码 */}
      {snippet.source_timecode_start && (
        <div className="text-xs text-gray-400 dark:text-gray-500">
          {snippet.source_timecode_start}
          {snippet.source_timecode_end && ` - ${snippet.source_timecode_end}`}
        </div>
      )}
    </div>
  );
}

/**
 * 时长徽章
 */
function DurationBadge({ seconds }: { seconds: number }) {
  const colors: Record<number, string> = {
    15: "bg-blue-500",
    30: "bg-green-500",
    60: "bg-purple-500",
  };

  return (
    <span
      className={`
        inline-flex items-center justify-center px-1.5 py-0.5 rounded text-xs font-bold text-white
        ${colors[seconds] || "bg-gray-500"}
      `}
    >
      {seconds}s
    </span>
  );
}

export default AdSnippetCard;
