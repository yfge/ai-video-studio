"use client";

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

const statusIcon = (status: WorkflowStepStatus) => {
  switch (status) {
    case "ready":
      return <span className="text-green-600">✓</span>;
    case "generating":
      return <span className="animate-pulse text-yellow-600">●</span>;
    default:
      return <span className="text-gray-400">○</span>;
  }
};

export function EpisodeWorkflowSteps({
  steps,
  compact = false,
}: EpisodeWorkflowStepsProps) {
  if (compact) {
    return (
      <div className="flex items-center gap-2 text-xs">
        {steps.map((step, index) => (
          <div key={step.key} className="flex items-center gap-1">
            {statusIcon(step.status)}
            <span
              className={
                step.status === "ready" ? "text-green-700" : "text-gray-600"
              }
            >
              {step.label}
            </span>
            {index < steps.length - 1 && (
              <span className="mx-1 text-gray-300">→</span>
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
                  {statusIcon(step.status)}
                </div>
                <div className="mt-1 text-sm font-semibold text-gray-900">
                  {step.label}
                </div>
                <p className="mt-1 text-xs text-gray-600">{step.description}</p>
                <button
                  onClick={step.onAction}
                  disabled={step.status === "generating"}
                  className="mt-3 inline-flex h-8 items-center rounded-md bg-blue-600 px-3 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {step.status === "generating"
                    ? "生成中..."
                    : step.actionLabel}
                </button>
              </div>
              {index < steps.length - 1 && (
                <div className="hidden items-center justify-center px-2 text-gray-300 md:flex">
                  →
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
