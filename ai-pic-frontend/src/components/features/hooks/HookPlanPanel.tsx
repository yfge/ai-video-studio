"use client";

import React, { useState } from "react";
import { HookTagBadge } from "./HookTagBadge";
import { AdSnippetCard, AdSnippetData } from "./AdSnippetCard";

/**
 * HookBeat 数据类型
 */
export interface HookBeatData {
  beat_type?: string;
  description: string;
  timing?: string;
  intensity?: string;
}

/**
 * HookPlan 数据类型
 */
export interface HookPlanData {
  opening_hook?: string;
  escalation_plan?: string;
  payoff_plan?: string;
  key_reversals?: HookBeatData[];
}

interface HookPlanPanelProps {
  /** Hook 计划数据 */
  hookPlan?: HookPlanData | null;
  /** 投流素材列表 */
  adSnippets?: AdSnippetData[] | null;
  /** 反转密度 */
  twistDensity?: string | null;
  /** 悬念卡点列表 */
  cliffhangerPlan?: string[] | null;
  /** 是否默认展开 */
  defaultExpanded?: boolean;
  /** 额外的 className */
  className?: string;
}

/**
 * Hook 计划面板组件
 *
 * 显示剧集/剧本的 hook 计划概览，包括：
 * - 开场钩子
 * - 情绪升级计划
 * - 爽点释放计划
 * - 关键反转列表
 * - 投流素材预览
 */
export function HookPlanPanel({
  hookPlan,
  adSnippets,
  twistDensity,
  cliffhangerPlan,
  defaultExpanded = false,
  className = "",
}: HookPlanPanelProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  const hasContent =
    hookPlan?.opening_hook ||
    hookPlan?.escalation_plan ||
    hookPlan?.payoff_plan ||
    (hookPlan?.key_reversals && hookPlan.key_reversals.length > 0) ||
    (adSnippets && adSnippets.length > 0) ||
    (cliffhangerPlan && cliffhangerPlan.length > 0);

  if (!hasContent) {
    return null;
  }

  return (
    <div
      className={`
        border rounded-lg bg-white dark:bg-gray-900
        border-gray-200 dark:border-gray-700
        ${className}
      `}
    >
      {/* 头部 */}
      <button
        className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-50 dark:hover:bg-gray-800 rounded-t-lg"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <span className="text-lg">🎬</span>
          <span className="font-medium text-gray-900 dark:text-gray-100">
            Hook 计划
          </span>
          {twistDensity && (
            <span className="text-xs text-gray-500 dark:text-gray-400">
              反转密度: {twistDensity}
            </span>
          )}
        </div>
        <span className="text-gray-400">{expanded ? "▼" : "▶"}</span>
      </button>

      {/* 内容 */}
      {expanded && (
        <div className="px-4 pb-4 space-y-4">
          {/* 核心钩子结构 */}
          {hookPlan && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {hookPlan.opening_hook && (
                <HookSection
                  title="开场钩子"
                  icon="🪝"
                  content={hookPlan.opening_hook}
                  color="orange"
                />
              )}
              {hookPlan.escalation_plan && (
                <HookSection
                  title="情绪升级"
                  icon="📈"
                  content={hookPlan.escalation_plan}
                  color="blue"
                />
              )}
              {hookPlan.payoff_plan && (
                <HookSection
                  title="爽点释放"
                  icon="🎯"
                  content={hookPlan.payoff_plan}
                  color="green"
                />
              )}
            </div>
          )}

          {/* 关键反转列表 */}
          {hookPlan?.key_reversals && hookPlan.key_reversals.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                关键反转 ({hookPlan.key_reversals.length})
              </h4>
              <div className="flex flex-wrap gap-2">
                {hookPlan.key_reversals.map((reversal, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-2 p-2 rounded bg-gray-50 dark:bg-gray-800 text-sm"
                  >
                    <HookTagBadge
                      hookType={reversal.beat_type || "reversal"}
                      intensity={reversal.intensity}
                      showLabel={false}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="text-gray-900 dark:text-gray-100">
                        {reversal.description}
                      </div>
                      {reversal.timing && (
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {reversal.timing}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 悬念卡点 */}
          {cliffhangerPlan && cliffhangerPlan.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                悬念卡点 ({cliffhangerPlan.length})
              </h4>
              <div className="flex flex-wrap gap-2">
                {cliffhangerPlan.map((cliff, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1 px-2 py-1 rounded bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-xs"
                  >
                    <span>⏸️</span>
                    {cliff}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* 投流素材预览 */}
          {adSnippets && adSnippets.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                投流素材 ({adSnippets.length})
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                {adSnippets.slice(0, 6).map((snippet, idx) => (
                  <AdSnippetCard key={idx} snippet={snippet} compact />
                ))}
              </div>
              {adSnippets.length > 6 && (
                <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
                  还有 {adSnippets.length - 6} 条素材...
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Hook 区块组件
 */
function HookSection({
  title,
  icon,
  content,
  color,
}: {
  title: string;
  icon: string;
  content: string;
  color: "orange" | "blue" | "green";
}) {
  const colorClasses = {
    orange: "bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800",
    blue: "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800",
    green: "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800",
  };

  return (
    <div className={`rounded-lg border p-3 ${colorClasses[color]}`}>
      <div className="flex items-center gap-1.5 mb-1.5">
        <span>{icon}</span>
        <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
          {title}
        </span>
      </div>
      <div className="text-sm text-gray-900 dark:text-gray-100">{content}</div>
    </div>
  );
}

export default HookPlanPanel;
