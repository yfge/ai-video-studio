"use client";

import React from "react";

/**
 * Hook 类型对应的样式配置
 */
const HOOK_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  hook: {
    bg: "bg-orange-100 dark:bg-orange-900/30",
    text: "text-orange-700 dark:text-orange-300",
    label: "钩子",
  },
  reversal: {
    bg: "bg-purple-100 dark:bg-purple-900/30",
    text: "text-purple-700 dark:text-purple-300",
    label: "反转",
  },
  payoff: {
    bg: "bg-green-100 dark:bg-green-900/30",
    text: "text-green-700 dark:text-green-300",
    label: "爽点",
  },
  cliffhanger: {
    bg: "bg-red-100 dark:bg-red-900/30",
    text: "text-red-700 dark:text-red-300",
    label: "卡点",
  },
  betrayal: {
    bg: "bg-red-100 dark:bg-red-900/30",
    text: "text-red-700 dark:text-red-300",
    label: "背叛",
  },
  reveal: {
    bg: "bg-blue-100 dark:bg-blue-900/30",
    text: "text-blue-700 dark:text-blue-300",
    label: "揭露",
  },
  revenge: {
    bg: "bg-amber-100 dark:bg-amber-900/30",
    text: "text-amber-700 dark:text-amber-300",
    label: "复仇",
  },
  reunion: {
    bg: "bg-pink-100 dark:bg-pink-900/30",
    text: "text-pink-700 dark:text-pink-300",
    label: "重逢",
  },
  threat: {
    bg: "bg-gray-100 dark:bg-gray-900/30",
    text: "text-gray-700 dark:text-gray-300",
    label: "威胁",
  },
  taboo: {
    bg: "bg-rose-100 dark:bg-rose-900/30",
    text: "text-rose-700 dark:text-rose-300",
    label: "禁忌",
  },
  "power-shift": {
    bg: "bg-indigo-100 dark:bg-indigo-900/30",
    text: "text-indigo-700 dark:text-indigo-300",
    label: "权力转移",
  },
};

const DEFAULT_STYLE = {
  bg: "bg-gray-100 dark:bg-gray-800",
  text: "text-gray-600 dark:text-gray-400",
  label: "标记",
};

interface HookTagBadgeProps {
  /** hook 类型：hook/reversal/payoff/cliffhanger/betrayal/reveal/revenge/reunion/threat/taboo/power-shift */
  hookType: string;
  /** 强度：low/medium/high */
  intensity?: string;
  /** 是否显示完整标签（否则只显示图标） */
  showLabel?: boolean;
  /** 点击回调 */
  onClick?: () => void;
  /** 额外的 className */
  className?: string;
}

/**
 * Hook 标签徽章组件
 *
 * 用于在分镜帧上显示 hook 类型（钩子/反转/爽点/卡点等）
 */
export function HookTagBadge({
  hookType,
  intensity,
  showLabel = true,
  onClick,
  className = "",
}: HookTagBadgeProps) {
  const normalizedType = hookType?.toLowerCase().replace(/\s+/g, "-") || "";
  const style = HOOK_STYLES[normalizedType] || DEFAULT_STYLE;

  // 强度对应的边框样式
  const intensityBorder =
    intensity === "high"
      ? "ring-2 ring-offset-1 ring-current"
      : intensity === "medium"
        ? "ring-1 ring-current"
        : "";

  return (
    <span
      className={`
        inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium
        ${style.bg} ${style.text} ${intensityBorder}
        ${onClick ? "cursor-pointer hover:opacity-80" : ""}
        ${className}
      `}
      onClick={onClick}
      title={`${style.label}${intensity ? ` (${intensity})` : ""}`}
    >
      <HookIcon type={normalizedType} />
      {showLabel && <span>{style.label}</span>}
    </span>
  );
}

/**
 * Hook 类型图标
 */
function HookIcon({ type }: { type: string }) {
  switch (type) {
    case "hook":
      return <span>🪝</span>;
    case "reversal":
      return <span>🔄</span>;
    case "payoff":
      return <span>🎯</span>;
    case "cliffhanger":
      return <span>⏸️</span>;
    case "betrayal":
      return <span>🗡️</span>;
    case "reveal":
      return <span>👁️</span>;
    case "revenge":
      return <span>⚔️</span>;
    case "reunion":
      return <span>🤝</span>;
    case "threat":
      return <span>⚠️</span>;
    case "taboo":
      return <span>🚫</span>;
    case "power-shift":
      return <span>👑</span>;
    default:
      return <span>📌</span>;
  }
}

export default HookTagBadge;
