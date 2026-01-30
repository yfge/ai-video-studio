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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
      <div
        className={`relative w-full ${widthClassName} rounded-2xl bg-white shadow-2xl`}
      >
        <div className="flex items-start gap-3 border-b px-6 py-5">
          {icon ? (
            <div className="flex h-11 w-11 items-center justify-center rounded-full bg-gradient-to-r from-blue-600 to-purple-600 text-white">
              {icon}
            </div>
          ) : null}
          <div className="flex-1">
            <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
            {subtitle ? (
              <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
            ) : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-1 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
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

        <div className="max-h-[70vh] overflow-y-auto px-6 py-5">{children}</div>

        {footer ? (
          <div className="flex justify-end gap-3 border-t px-6 py-4">
            {footer}
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default CreationOverlay;
