"use client";

import { useState } from "react";
import type {
  QuickFixResponse,
  ReadinessCheck,
  ReadinessResult,
} from "@/utils/api/types";
import {
  OperatorState,
  StatusPill,
  operatorButtonClass,
} from "@/components/shared";

interface StoryReadinessPanelProps {
  readiness: ReadinessResult | null;
  loading: boolean;
  error: string | null;
  quickFixLoading: boolean;
  onRefreshReadiness: () => void;
  onQuickFix: (dryRun: boolean) => Promise<QuickFixResponse | null>;
}

const fixableNames = new Set([
  "synopsis_present",
  "main_conflict_present",
  "setting_present",
  "world_building_present",
]);

const severityTone = (check: ReadinessCheck) => {
  if (check.passed) return "green";
  if (check.severity === "CRITICAL" || check.severity === "ERROR") return "red";
  if (check.severity === "WARNING") return "amber";
  return "blue";
};

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

  if (loading) return <OperatorState title="检查生成就绪状态..." />;
  if (error) {
    return (
      <OperatorState
        title={`就绪检查失败: ${error}`}
        tone="red"
        action={
          <button
            type="button"
            onClick={onRefreshReadiness}
            className={operatorButtonClass("secondary")}
          >
            重试
          </button>
        }
      />
    );
  }
  if (!readiness) {
    return (
      <OperatorState
        title="尚未检查生成就绪状态"
        action={
          <button
            type="button"
            onClick={onRefreshReadiness}
            className={operatorButtonClass("secondary")}
          >
            开始检查
          </button>
        }
      />
    );
  }

  const failedChecks = readiness.checks.filter((check) => !check.passed);
  const displayChecks = showAllChecks ? readiness.checks : failedChecks;
  const hasFixableIssues = readiness.checks.some(
    (check) => !check.passed && fixableNames.has(check.name),
  );

  return (
    <div className="space-y-3">
      <div className="rounded-md border border-gray-200 bg-gray-50 p-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-sm font-medium text-gray-950">
              {readiness.summary}
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              <StatusPill tone={readiness.ready ? "green" : "amber"}>
                通过 {readiness.passed_count}
              </StatusPill>
              <StatusPill tone={readiness.failed_count ? "red" : "gray"}>
                失败 {readiness.failed_count}
              </StatusPill>
              {readiness.warnings.length ? (
                <StatusPill tone="amber">
                  警告 {readiness.warnings.length}
                </StatusPill>
              ) : null}
            </div>
          </div>
          <button
            type="button"
            onClick={onRefreshReadiness}
            className={operatorButtonClass("ghost")}
          >
            刷新
          </button>
        </div>
      </div>

      {displayChecks.length ? (
        <div className="space-y-2">
          {displayChecks.map((check) => (
            <CheckItem key={check.name} check={check} />
          ))}
        </div>
      ) : (
        <OperatorState title="所有检查已通过" tone="green" />
      )}

      {readiness.passed_count > 0 ? (
        <button
          type="button"
          onClick={() => setShowAllChecks((value) => !value)}
          className={operatorButtonClass("ghost")}
        >
          {showAllChecks ? "只显示失败项" : `显示全部 ${readiness.checks.length} 项`}
        </button>
      ) : null}

      {hasFixableIssues && !readiness.ready ? (
        <QuickFixBox
          preview={quickFixPreview}
          loading={quickFixLoading}
          onPreview={async () => setQuickFixPreview(await onQuickFix(true))}
          onCancel={() => setQuickFixPreview(null)}
          onApply={async () => {
            await onQuickFix(false);
            setQuickFixPreview(null);
            onRefreshReadiness();
          }}
        />
      ) : null}

      {!readiness.can_proceed ? (
        <OperatorState
          title="存在严重问题，无法继续生成剧集"
          detail="请先修复 CRITICAL 项。"
          tone="red"
        />
      ) : null}
    </div>
  );
}

function CheckItem({ check }: { check: ReadinessCheck }) {
  return (
    <div className="rounded-md border border-gray-200 bg-white p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-sm font-medium text-gray-900">{check.message}</div>
          {!check.passed && check.suggestion ? (
            <div className="mt-1 text-xs text-gray-500">{check.suggestion}</div>
          ) : null}
        </div>
        <StatusPill tone={severityTone(check)}>{check.severity}</StatusPill>
      </div>
    </div>
  );
}

function QuickFixBox({
  preview,
  loading,
  onPreview,
  onCancel,
  onApply,
}: {
  preview: QuickFixResponse | null;
  loading: boolean;
  onPreview: () => Promise<void>;
  onCancel: () => void;
  onApply: () => Promise<void>;
}) {
  if (!preview) {
    return (
      <button
        type="button"
        onClick={() => void onPreview()}
        disabled={loading}
        className={operatorButtonClass("primary")}
      >
        {loading ? "生成中..." : "预览修复"}
      </button>
    );
  }
  return (
    <div className="rounded-md border border-gray-200 bg-gray-50 p-3">
      <div className="text-sm font-medium text-gray-950">
        将修复 {preview.improvement.fixed_count} 项
      </div>
      <div className="mt-2 space-y-1 text-xs text-gray-600">
        {preview.fixes_applied.slice(0, 4).map((fix, index) => (
          <div key={index}>
            {fix.field}: {fix.new_value.slice(0, 60)}
          </div>
        ))}
      </div>
      <div className="mt-3 flex gap-2">
        <button
          type="button"
          onClick={() => void onApply()}
          disabled={loading}
          className={operatorButtonClass("primary")}
        >
          确认应用
        </button>
        <button
          type="button"
          onClick={onCancel}
          className={operatorButtonClass("secondary")}
        >
          取消
        </button>
      </div>
    </div>
  );
}
