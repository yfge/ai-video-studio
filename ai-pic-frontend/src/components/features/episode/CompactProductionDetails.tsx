"use client";

import type { ReactNode } from "react";

const SUMMARY_BASE_CLASS = [
  "inline-flex shrink-0 cursor-pointer list-none items-center justify-center",
  "gap-1 rounded-md border text-[11px] font-medium transition",
  "marker:hidden [&::-webkit-details-marker]:hidden",
].join(" ");
const SUMMARY_TONE_CLASS = {
  default:
    "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900",
  primary:
    "border-blue-200 bg-blue-50 text-blue-700 hover:border-blue-300 hover:bg-blue-100 hover:text-blue-800",
};
const ATTACHED_TONE_CLASS = {
  default:
    "border-slate-200 bg-white text-slate-600 hover:bg-slate-50 hover:text-slate-900",
  primary: "border-blue-600 bg-blue-600 text-white hover:bg-blue-700",
};

const PANEL_ALIGN_CLASS = {
  left: "left-0",
  right: "right-0",
};

export function CompactParameterIcon() {
  return (
    <svg
      aria-hidden="true"
      className="h-3.5 w-3.5"
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.7"
      viewBox="0 0 16 16"
    >
      <path d="M3 4h10" />
      <path d="M3 8h10" />
      <path d="M3 12h10" />
      <path d="M6 2.8v2.4" />
      <path d="M10 6.8v2.4" />
      <path d="M7.5 10.8v2.4" />
    </svg>
  );
}

export function CompactProductionDetails({
  label,
  ariaLabel,
  align = "right",
  tone = "default",
  attached = false,
  children,
}: {
  label: string;
  ariaLabel: string;
  align?: "left" | "right";
  tone?: "default" | "primary";
  attached?: boolean;
  children: ReactNode;
}) {
  const iconOnly = label === "...";
  const triggerShape = iconOnly
    ? attached
      ? "attached-more"
      : "micro-more"
    : "label";
  return (
    <details
      data-clip-parameter-details="compact"
      className="group relative shrink-0"
    >
      <summary
        data-clip-parameter-summary="ghost"
        data-clip-parameter-trigger-shape={triggerShape}
        data-clip-parameter-tone={tone}
        className={`${SUMMARY_BASE_CLASS} ${
          iconOnly
            ? attached
              ? "h-8 w-7 rounded-l-none rounded-r-md border-l-0 px-0"
              : "h-6 w-6 rounded-full px-0"
            : "h-8 min-w-[3.25rem] px-2"
        } ${attached ? ATTACHED_TONE_CLASS[tone] : SUMMARY_TONE_CLASS[tone]}`}
        aria-label={ariaLabel}
        title={ariaLabel}
      >
        {iconOnly ? (
          <span data-clip-parameter-icon="controls">
            <CompactParameterIcon />
          </span>
        ) : (
          <>
            <CompactParameterIcon />
            <span>{label}</span>
          </>
        )}
      </summary>
      <div
        className={`${PANEL_ALIGN_CLASS[align]} absolute top-full z-30 mt-2 hidden max-h-[min(70vh,32rem)] w-[min(34rem,calc(100vw-2rem))] overflow-y-auto rounded-lg border border-gray-200 bg-white p-3 shadow-xl group-open:block`}
      >
        {children}
      </div>
    </details>
  );
}
