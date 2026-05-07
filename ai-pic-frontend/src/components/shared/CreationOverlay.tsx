"use client";

import { ReactNode } from "react";

interface CreationOverlayProps {
  open: boolean;
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  widthClassName?: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
}

export function CreationOverlay({
  open,
  title,
  subtitle,
  icon,
  widthClassName = "max-w-3xl",
  onClose,
  children,
  footer,
}: CreationOverlayProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-950/45 px-4">
      <div
        className={`relative w-full ${widthClassName} rounded-lg border border-gray-200 bg-white shadow-xl`}
      >
        <div className="flex items-start gap-3 border-b border-gray-200 px-5 py-4">
          {icon ? (
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-gray-950 text-white">
              {icon}
            </div>
          ) : null}
          <div className="flex-1">
            <h2 className="text-base font-semibold text-gray-950">{title}</h2>
            {subtitle ? (
              <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
            ) : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-gray-400 transition hover:bg-gray-100 hover:text-gray-700"
            aria-label="关闭"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <div className="max-h-[72vh] overflow-y-auto px-5 py-4">{children}</div>

        {footer ? (
          <div className="flex justify-end gap-3 border-t border-gray-200 px-5 py-4">
            {footer}
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default CreationOverlay;
