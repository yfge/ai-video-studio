"use client";

type TimelineToolbarIconKind = "view" | "fit" | "reset";

export function TimelineToolbarIcon({
  kind,
}: {
  kind: TimelineToolbarIconKind;
}) {
  if (kind === "view") {
    return (
      <svg
        aria-hidden="true"
        data-timeline-toolbar-icon="zoom"
        className="h-3.5 w-3.5"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.7"
        viewBox="0 0 16 16"
      >
        <circle cx="7" cy="7" r="4" />
        <path d="m10.2 10.2 3.1 3.1" />
        <path d="M7 5v4" />
        <path d="M5 7h4" />
      </svg>
    );
  }

  if (kind === "fit") {
    return (
      <svg
        aria-hidden="true"
        data-timeline-toolbar-icon="fit"
        className="h-3.5 w-3.5"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.7"
        viewBox="0 0 16 16"
      >
        <path d="M3 6V3h3" />
        <path d="M13 6V3h-3" />
        <path d="M3 10v3h3" />
        <path d="M13 10v3h-3" />
      </svg>
    );
  }

  return (
    <svg
      aria-hidden="true"
      data-timeline-toolbar-icon="reset"
      className="h-3.5 w-3.5"
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.7"
      viewBox="0 0 16 16"
    >
      <path d="M5 4.5h5.5a2.5 2.5 0 0 1 0 5H6" />
      <path d="M7 2.5 5 4.5l2 2" />
    </svg>
  );
}
