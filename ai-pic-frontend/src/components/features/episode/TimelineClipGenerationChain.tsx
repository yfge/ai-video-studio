"use client";

import type { TimelineClipProductionReadiness } from "./TimelineClipProductionReadiness";

type StepState = "ready" | "pending" | "blocked";

interface ChainStep {
  label: string;
  state: StepState;
  detail: string;
}

export function TimelineClipGenerationChain({
  readiness,
}: {
  readiness: TimelineClipProductionReadiness;
}) {
  const steps: ChainStep[] = [
    {
      label: "选参考/绑定",
      state: "ready",
      detail: "IP、环境和手动参考会随任务提交",
    },
    {
      label: "生图：分镜图",
      state: readiness.storyboardReady ? "ready" : "pending",
      detail: readiness.storyboardReady ? "已生成" : "先生成片段分镜图",
    },
    {
      label: "生图：首尾帧",
      state: readiness.keyframesReady ? "ready" : "pending",
      detail: readiness.keyframeStatus.label,
    },
    {
      label: "人工复核",
      state: readiness.humanReviewReady ? "ready" : "blocked",
      detail: readiness.humanReviewLabel,
    },
    {
      label: "生视频：片段视频",
      state: readiness.canGenerateVideo ? "ready" : "blocked",
      detail:
        readiness.humanReviewRequired && !readiness.humanReviewReady
          ? "等待人工复核"
          : readiness.videoGateMessage || "可以生成片段视频",
    },
  ];

  return (
    <section
      aria-label="片段生图生视频链路"
      data-clip-generation-chain="true"
      className="mb-2 grid gap-1.5 rounded-md border border-blue-100 bg-blue-50/60 p-2 text-[11px] text-slate-700 min-[760px]:grid-cols-5"
    >
      {steps.map((step, index) => (
        <div
          key={step.label}
          data-clip-generation-chain-step={step.state}
          className="grid min-w-0 grid-cols-[auto_minmax(0,1fr)] items-center gap-x-1.5 gap-y-0.5"
        >
          <span
            aria-hidden="true"
            className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-semibold ${
              step.state === "ready"
                ? "bg-green-100 text-green-700"
                : step.state === "blocked"
                ? "bg-amber-100 text-amber-700"
                : "bg-white text-slate-500"
            }`}
          >
            {index + 1}
          </span>
          <span className="min-w-0 truncate font-semibold text-slate-900">
            {step.label}
          </span>
          <span className="col-start-2 min-w-0 truncate text-slate-500">
            {step.detail}
          </span>
        </div>
      ))}
    </section>
  );
}
