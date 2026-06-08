"use client";

/**
 * Hook 类型对应的样式配置
 */
const HOOK_STYLES: Record<
  string,
  { bg: string; text: string; label: string; code: string }
> = {
  hook: {
    bg: "bg-gray-100 dark:bg-gray-800",
    text: "text-gray-700 dark:text-gray-300",
    label: "钩子",
    code: "H",
  },
  reversal: {
    bg: "bg-gray-100 dark:bg-gray-800",
    text: "text-gray-700 dark:text-gray-300",
    label: "反转",
    code: "R",
  },
  payoff: {
    bg: "bg-gray-100 dark:bg-gray-800",
    text: "text-gray-700 dark:text-gray-300",
    label: "爽点",
    code: "P",
  },
  cliffhanger: {
    bg: "bg-gray-100 dark:bg-gray-800",
    text: "text-gray-700 dark:text-gray-300",
    label: "卡点",
    code: "C",
  },
  betrayal: {
    bg: "bg-gray-100 dark:bg-gray-800",
    text: "text-gray-700 dark:text-gray-300",
    label: "背叛",
    code: "B",
  },
  reveal: {
    bg: "bg-gray-100 dark:bg-gray-800",
    text: "text-gray-700 dark:text-gray-300",
    label: "揭露",
    code: "V",
  },
  revenge: {
    bg: "bg-gray-100 dark:bg-gray-800",
    text: "text-gray-700 dark:text-gray-300",
    label: "复仇",
    code: "X",
  },
  reunion: {
    bg: "bg-gray-100 dark:bg-gray-800",
    text: "text-gray-700 dark:text-gray-300",
    label: "重逢",
    code: "U",
  },
  threat: {
    bg: "bg-gray-100 dark:bg-gray-800",
    text: "text-gray-700 dark:text-gray-300",
    label: "威胁",
    code: "T",
  },
  taboo: {
    bg: "bg-gray-100 dark:bg-gray-800",
    text: "text-gray-700 dark:text-gray-300",
    label: "禁忌",
    code: "N",
  },
  "power-shift": {
    bg: "bg-gray-100 dark:bg-gray-800",
    text: "text-gray-700 dark:text-gray-300",
    label: "权力转移",
    code: "S",
  },
};

const DEFAULT_STYLE = {
  bg: "bg-gray-100 dark:bg-gray-800",
  text: "text-gray-600 dark:text-gray-400",
  label: "标记",
  code: "M",
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
      <span className="font-mono text-[10px]">{style.code}</span>
      {showLabel && <span>{style.label}</span>}
    </span>
  );
}

export default HookTagBadge;
