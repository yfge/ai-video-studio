"use client";

import type { ReactNode } from "react";

type ClipProductionActionTone = "default" | "primary";

const MOBILE_LAYOUT_CLASS = {
  storyboard: "max-[719px]:order-1",
  keyframes: "max-[719px]:order-2",
  video: "max-[719px]:order-3 max-[719px]:col-span-2",
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
      className={`min-w-0 ${MOBILE_LAYOUT_CLASS[kind]}`}
    >
      <div data-clip-command-card-actions="inline" className="min-w-0">
        {children}
      </div>
      <div
        data-clip-command-card-header="step"
        className="hidden"
        aria-hidden="true"
      >
        <span data-clip-command-step={step} />
        <span data-clip-command-title={title} />
      </div>
    </section>
  );
}
