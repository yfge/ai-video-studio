"use client";

type ClipProductionActionIconKind = "storyboard" | "keyframes" | "video";

export function ClipProductionActionIcon({
  kind,
}: {
  kind: ClipProductionActionIconKind;
}) {
  if (kind === "storyboard") {
    return (
      <svg
        aria-hidden="true"
        className="h-3.5 w-3.5 shrink-0"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.7"
        viewBox="0 0 16 16"
      >
        <rect height="10" rx="1.4" width="12" x="2" y="3" />
        <path d="M6 3v10" />
        <path d="M10 3v10" />
      </svg>
    );
  }

  if (kind === "keyframes") {
    return (
      <svg
        aria-hidden="true"
        className="h-3.5 w-3.5 shrink-0"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.7"
        viewBox="0 0 16 16"
      >
        <path d="M3 4.5h10" />
        <path d="M3 11.5h10" />
        <path d="m5.5 2.5 2 2-2 2-2-2 2-2Z" />
        <path d="m10.5 9.5 2 2-2 2-2-2 2-2Z" />
      </svg>
    );
  }

  return (
    <svg
      aria-hidden="true"
      className="h-3.5 w-3.5 shrink-0"
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.8"
      viewBox="0 0 16 16"
    >
      <rect height="10" rx="1.5" width="12" x="2" y="3" />
      <path d="m7 6 3.5 2L7 10V6Z" fill="currentColor" stroke="none" />
    </svg>
  );
}
