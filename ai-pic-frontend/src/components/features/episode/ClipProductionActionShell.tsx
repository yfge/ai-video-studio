"use client";

import type { ReactNode } from "react";

type ClipProductionActionTone = "default" | "primary";

const MOBILE_LAYOUT_CLASS = {
  storyboard: "max-[719px]:order-1",
  keyframes: "max-[719px]:order-2",
  video: "max-[719px]:order-3 min-[720px]:max-[1179px]:col-span-2",
};

export function ClipProductionActionShell({
  kind,
  step,
  title,
  tone = "default",
  children,
}: {
  kind: "storyboard" | "keyframes" | "video";
  step: string;
  title: string;
  tone?: ClipProductionActionTone;
  children: ReactNode;
}) {
  return (
    <section
      data-clip-command-card={kind}
      data-clip-command-card-tone={tone}
      aria-label={`步骤 ${step} · ${title}`}
      className={`flex min-h-full min-w-0 flex-col rounded-xl border p-3 ${
        tone === "primary"
          ? "border-blue-200 bg-blue-50/40"
          : "border-slate-200 bg-white"
      } ${MOBILE_LAYOUT_CLASS[kind]}`}
    >
      <div
        data-clip-command-card-header="step"
        className="mb-2 flex items-center gap-2"
      >
        <span
          data-clip-command-step={step}
          className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold ${
            tone === "primary"
              ? "bg-blue-600 text-white"
              : "bg-slate-100 text-slate-600"
          }`}
        >
          {step}
        </span>
        <span
          data-clip-command-title={title}
          className="text-xs font-semibold text-slate-900"
        >
          {title}
        </span>
      </div>
      <div
        data-clip-command-card-actions="inline"
        className="flex min-h-0 min-w-0 flex-1 flex-col"
      >
        {children}
      </div>
    </section>
  );
}
