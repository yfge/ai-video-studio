"use client";

import { StatusPill } from "@/components/shared";

export function MetricCard({
  label,
  value,
  tone = "blue",
}: {
  label: string;
  value: number;
  tone?: "blue" | "green" | "red";
}) {
  const color =
    tone === "green"
      ? "text-green-700"
      : tone === "red"
        ? "text-red-700"
        : "text-blue-700";
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="text-xs text-gray-500">{label}</div>
      <div className={`mt-2 text-2xl font-semibold tabular-nums ${color}`}>
        {value}
      </div>
    </div>
  );
}

export function ReadyCell({ ready }: { ready: boolean }) {
  return (
    <td className="px-4 py-4">
      <StatusPill tone={ready ? "green" : "gray"}>
        {ready ? "已就绪" : "未开始"}
      </StatusPill>
    </td>
  );
}

export function AuditItem({
  label,
  value,
  tone = "green",
}: {
  label: string;
  value: string;
  tone?: "green" | "amber";
}) {
  return (
    <div className="rounded-md border border-gray-200 bg-white p-3">
      <div className="text-gray-500">{label}</div>
      <div
        className={tone === "green" ? "mt-1 text-green-700" : "mt-1 text-amber-700"}
      >
        {value}
      </div>
    </div>
  );
}
