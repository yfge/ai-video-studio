"use client";

import type { Script } from "@/utils/api/types";
import { formatDate } from "@/hooks/useScriptDetail";

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
    <header className="rounded-2xl bg-white p-6 shadow">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="flex items-center gap-3 text-sm text-gray-500">
            <button
              onClick={onNavigateToEpisode}
              className="text-blue-600 hover:text-blue-800"
            >
              返回剧集
            </button>
            <span>•</span>
            <span>剧本 #{script.id}</span>
          </div>
          <h1 className="mt-2 text-3xl font-bold text-gray-900">
            {script.title}
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            {script.format_type?.toUpperCase() || "剧本"} ·{" "}
            {script.language?.toUpperCase()} · 版本 {script.version || "1.0"}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onNavigateToStoryboard}
            className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700"
          >
            打开分镜
          </button>
          <div className="relative">
            <button
              onClick={() => setShowExportMenu(!showExportMenu)}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              导出剧本
            </button>
            {showExportMenu && (
              <div className="absolute right-0 mt-2 w-44 overflow-hidden rounded-md border border-gray-100 bg-white shadow-lg">
                <button
                  onClick={() => onExport("txt")}
                  className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
                >
                  导出 TXT
                </button>
                <button
                  onClick={() => onExport("pdf")}
                  className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
                >
                  导出 PDF
                </button>
                <button
                  onClick={() => onExport("docx")}
                  className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
                >
                  导出 DOCX
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
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
      <div className="mt-4 grid grid-cols-1 gap-4 text-sm text-gray-500 md:grid-cols-2">
        <div>创建时间：{formatDate(script.created_at)}</div>
        <div>更新时间：{formatDate(script.updated_at)}</div>
      </div>
    </header>
  );
}

function InfoCard({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string;
  value: React.ReactNode;
  hint?: string;
  tone?: "default" | "success" | "warning";
}) {
  const toneClass =
    tone === "success"
      ? "border-green-200 bg-green-50 text-green-700"
      : tone === "warning"
      ? "border-yellow-200 bg-yellow-50 text-yellow-700"
      : "border-gray-200 bg-white text-gray-900";
  return (
    <div className={`rounded-lg border p-4 shadow-sm ${toneClass}`}>
      <div className="text-xs uppercase tracking-wide text-gray-500">
        {label}
      </div>
      <div className="mt-2 text-lg font-semibold leading-6">{value}</div>
      {hint && <div className="mt-1 text-xs text-gray-500">{hint}</div>}
    </div>
  );
}
