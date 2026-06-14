import type { ReactNode } from "react";
import {
  OperatorPanel,
  OperatorSectionHeader,
  operatorClassNames,
} from "./OperatorPrimitives";

type WorkspaceVariant =
  | "main"
  | "rail-main"
  | "main-inspector"
  | "rail-main-inspector";

export function OperatorWorkspace({
  rail,
  main,
  inspector,
  variant = inspector ? "rail-main-inspector" : "rail-main",
  className,
}: {
  rail?: ReactNode;
  main: ReactNode;
  inspector?: ReactNode;
  variant?: WorkspaceVariant;
  className?: string;
}) {
  const gridClass =
    variant === "main"
      ? "grid-cols-1"
      : variant === "rail-main-inspector"
      ? "xl:grid-cols-[260px_minmax(0,1fr)_340px]"
      : variant === "main-inspector"
      ? "xl:grid-cols-[minmax(0,1fr)_360px]"
      : "xl:grid-cols-[300px_minmax(0,1fr)]";

  return (
    <div
      className={operatorClassNames(
        "grid h-[calc(100vh-8.5rem)] min-h-[620px] gap-4 overflow-hidden",
        gridClass,
        className,
      )}
    >
      {rail}
      {main}
      {inspector}
    </div>
  );
}

export function OperatorContextRail({
  title,
  subtitle,
  action,
  children,
  className,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <OperatorPanel
      className={operatorClassNames("min-h-0 overflow-hidden", className)}
    >
      <OperatorSectionHeader
        title={title}
        subtitle={subtitle}
        action={action}
      />
      <div className="min-h-0 overflow-y-auto p-3">{children}</div>
    </OperatorPanel>
  );
}

export function OperatorMainCanvas({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={operatorClassNames("min-h-0 overflow-y-auto pr-1", className)}
    >
      {children}
    </div>
  );
}

export function OperatorInspector({
  title,
  subtitle,
  action,
  children,
  className,
}: {
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <OperatorPanel
      className={operatorClassNames(
        "min-h-0 overflow-hidden xl:sticky xl:top-20 xl:max-h-[calc(100vh-5rem)] xl:self-start",
        className,
      )}
    >
      {title ? (
        <OperatorSectionHeader
          title={title}
          subtitle={subtitle}
          action={action}
        />
      ) : null}
      <div className="min-h-0 overflow-y-auto p-4">{children}</div>
    </OperatorPanel>
  );
}

export function OperatorToolbar({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={operatorClassNames(
        "flex flex-wrap items-center justify-between gap-3 rounded-lg border border-gray-200 bg-white px-4 py-3",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function OperatorEntityHeader({
  eyebrow,
  title,
  subtitle,
  meta,
  action,
}: {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  meta?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <OperatorPanel className="p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          {eyebrow ? (
            <div className="text-xs font-medium text-gray-500">{eyebrow}</div>
          ) : null}
          <h1 className="mt-1 truncate text-lg font-semibold text-gray-950">
            {title}
          </h1>
          {subtitle ? (
            <p className="mt-1 line-clamp-2 text-sm text-gray-600">
              {subtitle}
            </p>
          ) : null}
          {meta ? (
            <div className="mt-3 flex flex-wrap gap-2">{meta}</div>
          ) : null}
        </div>
        {action ? <div className="shrink-0">{action}</div> : null}
      </div>
    </OperatorPanel>
  );
}

export function OperatorTabs<T extends string>({
  tabs,
  active,
  onChange,
}: {
  tabs: Array<{ key: T; label: string; disabled?: boolean }>;
  active: T;
  onChange: (key: T) => void;
}) {
  return (
    <div className="border-b border-gray-200">
      <nav className="-mb-px flex gap-1 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            disabled={tab.disabled}
            onClick={() => onChange(tab.key)}
            className={operatorClassNames(
              "border-b-2 px-3 py-2 text-xs font-medium transition-colors",
              active === tab.key
                ? "border-blue-500 text-blue-700"
                : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-800",
              tab.disabled && "cursor-not-allowed opacity-40",
            )}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </div>
  );
}

export function OperatorListRow({
  selected,
  onClick,
  children,
  className,
}: {
  selected?: boolean;
  onClick?: () => void;
  children: ReactNode;
  className?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={operatorClassNames(
        "block w-full rounded-md border p-3 text-left transition-colors",
        selected
          ? "border-blue-200 bg-blue-50"
          : "border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50",
        className,
      )}
    >
      {children}
    </button>
  );
}
