import type { ReactNode } from "react";

type Tone = "neutral" | "blue" | "green" | "amber" | "red";
type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";

const join = (...classes: Array<string | false | null | undefined>) =>
  classes.filter(Boolean).join(" ");

export const operatorButtonClass = (
  variant: ButtonVariant = "secondary",
  className?: string,
) =>
  join(
    "inline-flex h-8 items-center justify-center rounded-md px-3 text-xs font-medium transition-colors",
    "disabled:pointer-events-none disabled:opacity-50",
    variant === "primary" && "bg-blue-600 text-white hover:bg-blue-700",
    variant === "secondary" &&
      "border border-gray-200 bg-white text-gray-700 hover:bg-gray-50",
    variant === "danger" && "bg-red-600 text-white hover:bg-red-700",
    variant === "ghost" && "text-gray-600 hover:bg-gray-100 hover:text-gray-950",
    className,
  );

export const operatorSelectClass = (className?: string) =>
  join(
    "h-8 rounded-md border border-gray-200 bg-white px-2 text-xs text-gray-800",
    "focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100",
    "disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-400",
    className,
  );

export const operatorInputClass = (className?: string) =>
  join(
    "h-8 rounded-md border border-gray-200 bg-white px-3 text-xs text-gray-800",
    "placeholder:text-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100",
    className,
  );

export function OperatorPanel({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={join("rounded-lg border border-gray-200 bg-white", className)}>
      {children}
    </section>
  );
}

export function OperatorSectionHeader({
  title,
  subtitle,
  action,
  className,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={join(
        "flex items-center justify-between gap-3 border-b border-gray-200 px-4 py-3",
        className,
      )}
    >
      <div className="min-w-0">
        <h2 className="truncate text-sm font-semibold text-gray-950">{title}</h2>
        {subtitle ? (
          <p className="mt-0.5 truncate text-xs text-gray-500">{subtitle}</p>
        ) : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}

export function OperatorState({
  title,
  detail,
  tone = "neutral",
  action,
}: {
  title: string;
  detail?: string;
  tone?: Tone;
  action?: ReactNode;
}) {
  const toneClass = {
    neutral: "border-gray-200 bg-white text-gray-600",
    blue: "border-blue-200 bg-blue-50 text-blue-700",
    green: "border-green-200 bg-green-50 text-green-700",
    amber: "border-amber-200 bg-amber-50 text-amber-700",
    red: "border-red-200 bg-red-50 text-red-700",
  }[tone];

  return (
    <div className={join("rounded-lg border p-4 text-sm", toneClass)}>
      <div className="font-medium">{title}</div>
      {detail ? <div className="mt-1 text-xs opacity-80">{detail}</div> : null}
      {action ? <div className="mt-3">{action}</div> : null}
    </div>
  );
}

export const operatorTableClass = "min-w-full text-sm";
export const operatorTableHeadClass =
  "bg-gray-50 text-xs font-medium text-gray-500";
export const operatorTableRowClass =
  "bg-white transition-colors hover:bg-blue-50/40";
