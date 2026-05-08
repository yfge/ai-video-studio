"use client";

import type { ReactNode } from "react";
import type { Script } from "@/utils/api/types";
import { formatDate } from "@/hooks/useScriptDetail";
import {
  OperatorPanel,
  OperatorSectionHeader,
  operatorButtonClass,
} from "@/components/shared";

interface ScriptHeaderProps {
  script: Script;
  showExportMenu: boolean;
  setShowExportMenu: (show: boolean) => void;
  onExport: (format: string) => void;
  onNavigateToEpisode: () => void;
  onNavigateToStoryboard: () => void;
}

export function ScriptHeader({
  script,
  showExportMenu,
  setShowExportMenu,
  onExport,
  onNavigateToEpisode,
  onNavigateToStoryboard,
}: ScriptHeaderProps) {
  return (
    <OperatorPanel>
      <OperatorSectionHeader
        title="剧本资产"
        subtitle={`剧本 #${script.id}`}
        action={
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onNavigateToEpisode}
              className={operatorButtonClass("secondary")}
            >
              返回剧集
            </button>
            <button
              type="button"
              onClick={onNavigateToStoryboard}
              className={operatorButtonClass("secondary")}
            >
              打开分镜
            </button>
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowExportMenu(!showExportMenu)}
                className={operatorButtonClass("primary")}
              >
                导出剧本
              </button>
              {showExportMenu && (
                <div className="absolute right-0 z-10 mt-2 w-36 overflow-hidden rounded-md border border-gray-200 bg-white shadow-lg">
                  {["txt", "pdf", "docx"].map((format) => (
                    <button
                      key={format}
                      type="button"
                      onClick={() => onExport(format)}
                      className="block w-full px-3 py-2 text-left text-xs text-gray-700 hover:bg-gray-50"
                    >
                      导出 {format.toUpperCase()}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        }
      />
      <div className="p-4">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div className="min-w-0">
            <h1 className="truncate text-lg font-semibold text-gray-950">
            {script.title}
            </h1>
            <p className="mt-1 text-xs text-gray-500">
            {script.format_type?.toUpperCase() || "剧本"} ·{" "}
            {script.language?.toUpperCase()} · 版本 {script.version || "1.0"}
            </p>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
        <InfoCard label="字数" value={script.word_count || 0} hint="字数统计" />
        <InfoCard
          label="字符数"
          value={script.character_count || 0}
          hint="字符统计"
        />
        <InfoCard label="页数" value={script.page_count || 0} hint="预计页数" />
        <InfoCard
          label="状态"
          value={
            script.status === "published"
              ? "已发布"
              : script.status === "approved"
              ? "已审核"
              : "草稿"
          }
          tone={
            script.status === "published"
              ? "success"
              : script.status === "approved"
              ? "warning"
              : "default"
          }
          hint={
            script.status === "draft"
              ? "可编辑"
              : script.status === "approved"
              ? "待发布"
              : "无需修改"
          }
        />
      </div>
        <div className="mt-4 grid grid-cols-1 gap-2 text-xs text-gray-500 md:grid-cols-2">
          <div>创建时间：{formatDate(script.created_at)}</div>
          <div>更新时间：{formatDate(script.updated_at)}</div>
        </div>
      </div>
    </OperatorPanel>
  );
}

function InfoCard({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  tone?: "default" | "success" | "warning";
}) {
  const toneClass =
    tone === "success"
      ? "border-green-200 bg-green-50 text-green-700"
      : tone === "warning"
      ? "border-yellow-200 bg-yellow-50 text-yellow-700"
      : "border-gray-200 bg-gray-50 text-gray-900";
  return (
    <div className={`rounded-md border p-3 ${toneClass}`}>
      <div className="text-xs text-gray-500">
        {label}
      </div>
      <div className="mt-1 text-sm font-semibold leading-6">{value}</div>
      {hint && <div className="mt-1 text-xs text-gray-500">{hint}</div>}
    </div>
  );
}
