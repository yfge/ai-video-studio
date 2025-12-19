"use client";

import type { Script } from "@/utils/api";
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
            <button onClick={onNavigateToEpisode} className="text-blue-600 hover:text-blue-800">
              Back to Episode
            </button>
            <span>•</span>
            <span>Script #{script.id}</span>
          </div>
          <h1 className="mt-2 text-3xl font-bold text-gray-900">{script.title}</h1>
          <p className="mt-1 text-sm text-gray-500">
            {script.format_type?.toUpperCase() || "Script"} · {script.language?.toUpperCase()} · Version{" "}
            {script.version || "1.0"}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onNavigateToStoryboard}
            className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700"
          >
            Open Storyboard
          </button>
          <div className="relative">
            <button
              onClick={() => setShowExportMenu(!showExportMenu)}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Export Script
            </button>
            {showExportMenu && (
              <div className="absolute right-0 mt-2 w-44 overflow-hidden rounded-md border border-gray-100 bg-white shadow-lg">
                <button
                  onClick={() => onExport("txt")}
                  className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
                >
                  Export as TXT
                </button>
                <button
                  onClick={() => onExport("pdf")}
                  className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
                >
                  Export as PDF
                </button>
                <button
                  onClick={() => onExport("docx")}
                  className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
                >
                  Export as DOCX
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <InfoCard label="Words" value={script.word_count || 0} hint="Word Count" />
        <InfoCard label="Characters" value={script.character_count || 0} hint="Character Count" />
        <InfoCard label="Pages" value={script.page_count || 0} hint="Estimated Pages" />
        <InfoCard
          label="Status"
          value={
            script.status === "published"
              ? "Published"
              : script.status === "approved"
              ? "Approved"
              : "Draft"
          }
          tone={
            script.status === "published" ? "success" : script.status === "approved" ? "warning" : "default"
          }
          hint={
            script.status === "draft"
              ? "Can be edited"
              : script.status === "approved"
              ? "Awaiting publish"
              : "No changes needed"
          }
        />
      </div>
      <div className="mt-4 grid grid-cols-1 gap-4 text-sm text-gray-500 md:grid-cols-2">
        <div>Created: {formatDate(script.created_at)}</div>
        <div>Updated: {formatDate(script.updated_at)}</div>
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
      <div className="text-xs uppercase tracking-wide text-gray-500">{label}</div>
      <div className="mt-2 text-lg font-semibold leading-6">{value}</div>
      {hint && <div className="mt-1 text-xs text-gray-500">{hint}</div>}
    </div>
  );
}
