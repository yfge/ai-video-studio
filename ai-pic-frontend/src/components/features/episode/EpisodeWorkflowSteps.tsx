"use client";

import { StatusPill, operatorButtonClass } from "@/components/shared";

export type WorkflowStepStatus = "pending" | "ready" | "generating";

export interface WorkflowStep {
  key: string;
  label: string;
  description: string;
  status: WorkflowStepStatus;
  actionLabel: string;
  onAction: () => void;
}

interface EpisodeWorkflowStepsProps {
  steps: WorkflowStep[];
  compact?: boolean;
}

const statusLabel = (status: WorkflowStepStatus) => {
  switch (status) {
    case "ready":
      return "已就绪";
    case "generating":
      return "生成中";
    default:
      return "待处理";
  }
};

const statusTone = (status: WorkflowStepStatus) =>
  status === "ready" ? "green" : status === "generating" ? "amber" : "gray";

export function EpisodeWorkflowSteps({
  steps,
  compact = false,
}: EpisodeWorkflowStepsProps) {
  if (compact) {
    return (
      <div className="flex items-center gap-2 text-xs">
        {steps.map((step, index) => (
          <div key={step.key} className="flex items-center gap-1">
            <StatusPill tone={statusTone(step.status)}>{step.label}</StatusPill>
            {index < steps.length - 1 && (
              <span className="mx-1 text-gray-300">/</span>
            )}
          </div>
        ))}
      </div>
    );
  }

  return (
    <section className="rounded-lg border border-gray-200 bg-white p-3">
      <div className="flex flex-col items-stretch gap-2 md:flex-row">
        {steps.map((step, index) => {
          return (
            <div key={step.key} className="flex flex-1 items-center">
              <div className="flex-1 rounded-md border border-gray-200 bg-white p-3">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-semibold text-blue-700">
                    步骤 {index + 1}
                  </div>
                  <StatusPill tone={statusTone(step.status)}>
                    {statusLabel(step.status)}
                  </StatusPill>
                </div>
                <div className="mt-1 text-sm font-semibold text-gray-900">
                  {step.label}
                </div>
                <p className="mt-1 text-xs text-gray-600">{step.description}</p>
                <button
                  onClick={step.onAction}
                  disabled={step.status === "generating"}
                  className={operatorButtonClass("secondary", "mt-3")}
                >
                  {step.status === "generating"
                    ? "生成中..."
                    : step.actionLabel}
                </button>
              </div>
              {index < steps.length - 1 && (
                <div className="hidden items-center justify-center px-2 text-gray-300 md:flex">
                  /
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
