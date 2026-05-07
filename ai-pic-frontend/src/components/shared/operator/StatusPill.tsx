import type { ReactNode } from "react";

type StatusTone = "blue" | "green" | "amber" | "red" | "gray";

const toneClass: Record<StatusTone, string> = {
  blue: "border-blue-200 bg-blue-50 text-blue-700",
  green: "border-green-200 bg-green-50 text-green-700",
  amber: "border-amber-200 bg-amber-50 text-amber-700",
  red: "border-red-200 bg-red-50 text-red-700",
  gray: "border-gray-200 bg-white text-gray-600",
};

export function StatusPill({
  children,
  tone = "gray",
}: {
  children: ReactNode;
  tone?: StatusTone;
}) {
  return (
    <span
      className={`inline-flex h-6 items-center whitespace-nowrap rounded-md border px-2 text-xs font-medium ${toneClass[tone]}`}
    >
      {children}
    </span>
  );
}

export const taskStatusTone = (status: string): StatusTone => {
  if (status === "completed") return "green";
  if (status === "processing") return "amber";
  if (status === "failed") return "red";
  if (status === "pending") return "blue";
  return "gray";
};
