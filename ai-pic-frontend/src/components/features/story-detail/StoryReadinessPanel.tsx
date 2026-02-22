"use client";

import { useState } from "react";
import type {
  ReadinessResult,
  ReadinessCheck,
  QuickFixResponse,
} from "@/utils/api/types";

interface StoryReadinessPanelProps {
  readiness: ReadinessResult | null;
  loading: boolean;
  error: string | null;
  quickFixLoading: boolean;
  onRefreshReadiness: () => void;
  onQuickFix: (dryRun: boolean) => Promise<QuickFixResponse | null>;
}

const SEVERITY_STYLES: Record<
  string,
  { bg: string; border: string; text: string; icon: string }
> = {
  CRITICAL: {
    bg: "bg-red-50",
    border: "border-red-200",
    text: "text-red-800",
    icon: "X",
  },
  ERROR: {
    bg: "bg-orange-50",
    border: "border-orange-200",
    text: "text-orange-800",
    icon: "!",
  },
  WARNING: {
    bg: "bg-yellow-50",
    border: "border-yellow-200",
    text: "text-yellow-700",
    icon: "?",
  },
  INFO: {
    bg: "bg-blue-50",
    border: "border-blue-200",
    text: "text-blue-700",
    icon: "i",
  },
};

function CheckItem({ check }: { check: ReadinessCheck }) {
  const style = SEVERITY_STYLES[check.severity] || SEVERITY_STYLES.INFO;
  return (
    <div
      className={`flex items-start gap-2 p-2 rounded ${style.bg} ${style.border} border`}
    >
      <span
        className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
          style.text
        } ${check.passed ? "bg-green-100 text-green-600" : ""}`}
      >
        {check.passed ? "✓" : style.icon}
      </span>
      <div className="flex-1 min-w-0">
        <div
          className={`text-sm font-medium ${
            check.passed ? "text-green-700" : style.text
          }`}
        >
          {check.message}
        </div>
        {!check.passed && check.suggestion && (
          <div className="text-xs text-gray-600 mt-1">{check.suggestion}</div>
        )}
      </div>
      <span
        className={`text-xs px-2 py-0.5 rounded ${
          check.passed ? "bg-green-100 text-green-700" : style.bg
        } ${style.text}`}
      >
        {check.severity}
      </span>
    </div>
  );
}

export function StoryReadinessPanel({
  readiness,
  loading,
  error,
  quickFixLoading,
  onRefreshReadiness,
  onQuickFix,
}: StoryReadinessPanelProps) {
  const [showAllChecks, setShowAllChecks] = useState(false);
  const [quickFixPreview, setQuickFixPreview] =
    useState<QuickFixResponse | null>(null);

  const handleQuickFixPreview = async () => {
    const result = await onQuickFix(true);
    setQuickFixPreview(result);
  };

  const handleQuickFixApply = async () => {
    await onQuickFix(false);
    setQuickFixPreview(null);
    onRefreshReadiness();
  };

  if (loading) {
    return (
      <div className="bg-gray-50 rounded-lg p-4 mb-4">
        <div className="flex items-center gap-2">
          <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
          <span className="text-sm text-gray-600">检查生成就绪状态...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-red-700">就绪检查失败: {error}</span>
          <button
            onClick={onRefreshReadiness}
            className="text-xs text-red-600 hover:text-red-800 underline"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  if (!readiness) {
    return (
      <div className="bg-gray-50 rounded-lg p-4 mb-4">
        <button
          onClick={onRefreshReadiness}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          检查生成就绪状态
        </button>
      </div>
    );
  }

  const hasFixableIssues = readiness.checks.some(
    (c) =>
      !c.passed &&
      [
        "synopsis_present",
        "main_conflict_present",
        "setting_present",
        "world_building_present",
      ].includes(c.name),
  );

  const failedChecks = readiness.checks.filter((c) => !c.passed);
  const displayChecks = showAllChecks ? readiness.checks : failedChecks;

  return (
    <div
      className={`rounded-lg p-4 mb-4 border ${
        readiness.ready
          ? "bg-green-50 border-green-200"
          : readiness.can_proceed
          ? "bg-yellow-50 border-yellow-200"
          : "bg-red-50 border-red-200"
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span
            className={`text-lg ${
              readiness.ready
                ? "text-green-600"
                : readiness.can_proceed
                ? "text-yellow-600"
                : "text-red-600"
            }`}
          >
            {readiness.ready ? "✓" : readiness.can_proceed ? "!" : "✗"}
          </span>
          <span
            className={`font-medium ${
              readiness.ready
                ? "text-green-800"
                : readiness.can_proceed
                ? "text-yellow-800"
                : "text-red-800"
            }`}
          >
            {readiness.summary}
          </span>
        </div>
        <button
          onClick={onRefreshReadiness}
          className="text-xs text-gray-500 hover:text-gray-700"
          title="刷新检查"
        >
          刷新
        </button>
      </div>

      {/* Stats bar */}
      <div className="flex items-center gap-4 text-xs text-gray-600 mb-3">
        <span>通过: {readiness.passed_count}</span>
        <span>失败: {readiness.failed_count}</span>
        {readiness.critical_issues.length > 0 && (
          <span className="text-red-600 font-medium">
            严重问题: {readiness.critical_issues.length}
          </span>
        )}
        {readiness.errors.length > 0 && (
          <span className="text-orange-600">
            错误: {readiness.errors.length}
          </span>
        )}
        {readiness.warnings.length > 0 && (
          <span className="text-yellow-600">
            警告: {readiness.warnings.length}
          </span>
        )}
      </div>

      {/* Failed checks */}
      {displayChecks.length > 0 && (
        <div className="space-y-2 mb-3">
          {displayChecks.map((check) => (
            <CheckItem key={check.name} check={check} />
          ))}
        </div>
      )}

      {/* Toggle all checks */}
      {readiness.passed_count > 0 && (
        <button
          onClick={() => setShowAllChecks(!showAllChecks)}
          className="text-xs text-gray-500 hover:text-gray-700 mb-3"
        >
          {showAllChecks
            ? "只显示失败项"
            : `显示全部 ${readiness.checks.length} 项检查`}
        </button>
      )}

      {/* Quick fix section */}
      {hasFixableIssues && !readiness.ready && (
        <div className="border-t border-gray-200 pt-3 mt-3">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-medium text-gray-700">一键补齐</span>
            <span className="text-xs text-gray-500">
              自动填充缺失的 synopsis/conflict/setting/world_building
            </span>
          </div>

          {quickFixPreview ? (
            <div className="bg-white rounded p-3 border mb-3">
              <div className="text-sm font-medium text-gray-800 mb-2">
                预览: 将修复 {quickFixPreview.improvement.fixed_count} 项
              </div>
              {quickFixPreview.fixes_applied.map((fix, i) => (
                <div key={i} className="text-xs text-gray-600 mb-1">
                  • {fix.field}: {fix.new_value.slice(0, 50)}...
                </div>
              ))}
              {quickFixPreview.fixes_skipped.length > 0 && (
                <div className="text-xs text-orange-600 mt-2">
                  跳过 {quickFixPreview.fixes_skipped.length} 项:{" "}
                  {quickFixPreview.fixes_skipped
                    .map((s) => s.reason)
                    .join(", ")}
                </div>
              )}
              <div className="flex gap-2 mt-3">
                <button
                  onClick={handleQuickFixApply}
                  disabled={quickFixLoading}
                  className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                >
                  {quickFixLoading ? "应用中..." : "确认应用"}
                </button>
                <button
                  onClick={() => setQuickFixPreview(null)}
                  className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                >
                  取消
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={handleQuickFixPreview}
              disabled={quickFixLoading}
              className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {quickFixLoading ? "生成中..." : "预览修复"}
            </button>
          )}
        </div>
      )}

      {/* Generation blocked warning */}
      {!readiness.can_proceed && (
        <div className="bg-red-100 border border-red-300 rounded p-2 mt-3">
          <span className="text-sm text-red-800 font-medium">
            存在严重问题，无法继续生成剧集。请先修复上述标记为 CRITICAL 的问题。
          </span>
        </div>
      )}
    </div>
  );
}
