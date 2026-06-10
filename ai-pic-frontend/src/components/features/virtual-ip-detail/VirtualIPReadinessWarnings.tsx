"use client";

import type { VirtualIPReadiness } from "@/utils/api/types";

/**
 * Amber callout listing backend-computed production readiness gaps
 * (missing default avatar / incomplete voice binding). Non-blocking.
 */
export function VirtualIPReadinessWarnings({
  readiness,
}: {
  readiness?: VirtualIPReadiness | null;
}) {
  if (!readiness || readiness.warnings.length === 0) return null;
  return (
    <div
      className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3"
      role="alert"
    >
      <div className="text-sm font-semibold text-amber-900">
        生产就绪提醒（{readiness.warnings.length} 项待补齐）
      </div>
      <ul className="mt-1.5 list-disc space-y-1 pl-5 text-xs text-amber-800">
        {readiness.warnings.map((warning) => (
          <li key={warning}>{warning}</li>
        ))}
      </ul>
    </div>
  );
}
