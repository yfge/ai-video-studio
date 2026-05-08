import type { ReactNode } from "react";
import {
  OperatorSectionHeader,
  operatorButtonClass,
} from "./OperatorPrimitives";

export function OperatorModalFrame({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-950/35 p-4">
      <div className="w-full max-w-md overflow-hidden rounded-lg border border-gray-200 bg-white shadow-lg">
        <OperatorSectionHeader title={title} subtitle={subtitle} />
        <div className="p-4">{children}</div>
        {footer ? (
          <div className="flex justify-end gap-2 border-t border-gray-200 bg-gray-50 px-4 py-3">
            {footer}
          </div>
        ) : null}
      </div>
    </div>
  );
}

export function OperatorDrawer({
  open,
  title,
  subtitle,
  onClose,
  children,
}: {
  open: boolean;
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: ReactNode;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 bg-gray-950/30">
      <aside className="ml-auto flex h-full w-full max-w-md flex-col border-l border-gray-200 bg-white shadow-lg">
        <OperatorSectionHeader
          title={title}
          subtitle={subtitle}
          action={
            <button
              type="button"
              onClick={onClose}
              className={operatorButtonClass("ghost")}
            >
              关闭
            </button>
          }
        />
        <div className="min-h-0 flex-1 overflow-y-auto p-4">{children}</div>
      </aside>
    </div>
  );
}
