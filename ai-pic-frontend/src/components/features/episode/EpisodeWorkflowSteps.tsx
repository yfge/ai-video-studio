"use client";

export type WorkflowStepStatus = "pending" | "ready" | "generating";

export interface WorkflowStep {
  key: string;
  label: string;
  description: string;
  status: WorkflowStepStatus;
  actionLabel: string;
  onAction: () => void;
  color: "blue" | "indigo" | "purple";
}

interface EpisodeWorkflowStepsProps {
  steps: WorkflowStep[];
  compact?: boolean;
}

const colorMap = {
  blue: {
    bg: "from-blue-50 to-white",
    text: "text-blue-700",
    button: "bg-blue-600 hover:bg-blue-700",
  },
  indigo: {
    bg: "from-indigo-50 to-white",
    text: "text-indigo-700",
    button: "bg-indigo-600 hover:bg-indigo-700",
  },
  purple: {
    bg: "from-purple-50 to-white",
    text: "text-purple-700",
    button: "bg-purple-600 hover:bg-purple-700",
  },
};

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
      <div className="flex items-center gap-2 text-sm">
        {steps.map((step, index) => (
          <div key={step.key} className="flex items-center gap-1">
            {statusIcon(step.status)}
            <span className={step.status === "ready" ? "text-green-700" : "text-gray-600"}>
              {step.label}
            </span>
            {index < steps.length - 1 && <span className="text-gray-300 mx-1">→</span>}
          </div>
        ))}
      </div>
    );
  }

  return (
    <section className="grid gap-3 rounded-2xl bg-white p-4 shadow md:grid-cols-3">
      {steps.map((step, index) => {
        const colors = colorMap[step.color];
        return (
          <div
            key={step.key}
            className={`rounded-xl border border-gray-100 bg-gradient-to-br ${colors.bg} p-4`}
          >
            <div className="flex items-center justify-between">
              <div className={`text-xs font-semibold uppercase tracking-wide ${colors.text}`}>
                步骤 {index + 1}
              </div>
              {statusIcon(step.status)}
            </div>
            <div className="mt-1 text-base font-semibold text-gray-900">
              {step.label}
            </div>
            <p className="mt-1 text-xs text-gray-600">{step.description}</p>
            <button
              onClick={step.onAction}
              disabled={step.status === "generating"}
              className={`mt-3 inline-flex items-center rounded-lg ${colors.button} px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50`}
            >
              {step.status === "generating" ? "生成中..." : step.actionLabel}
            </button>
          </div>
        );
      })}
    </section>
  );
}
