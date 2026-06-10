"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  TOAST_DEFAULT_DURATION_MS,
  TOAST_MAX_VISIBLE,
  type NotifyVariant,
  type ToastItem,
  type ToastOptions,
} from "./toastTypes";

interface ToastContextValue {
  notify: (
    message: string,
    variant?: NotifyVariant,
    options?: ToastOptions,
  ) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

const VARIANT_CLASS: Record<NotifyVariant, string> = {
  success: "border-l-green-500 bg-green-50 text-green-800",
  error: "border-l-red-500 bg-red-50 text-red-800",
  warning: "border-l-amber-500 bg-amber-50 text-amber-800",
  info: "border-l-blue-500 bg-blue-50 text-blue-800",
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextIdRef = useRef(1);
  const timersRef = useRef(new Map<number, ReturnType<typeof setTimeout>>());

  useEffect(() => {
    const timers = timersRef.current;
    return () => {
      for (const timer of timers.values()) clearTimeout(timer);
      timers.clear();
    };
  }, []);

  const dismiss = useCallback((id: number) => {
    const timer = timersRef.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timersRef.current.delete(id);
    }
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const notify = useCallback(
    (
      message: string,
      variant: NotifyVariant = "info",
      options?: ToastOptions,
    ) => {
      const id = nextIdRef.current++;
      const durationMs =
        options?.durationMs ?? TOAST_DEFAULT_DURATION_MS[variant];
      setToasts((prev) => {
        const next = [
          { id, message, variant, title: options?.title, durationMs },
          ...prev,
        ];
        for (const dropped of next.slice(TOAST_MAX_VISIBLE)) {
          const timer = timersRef.current.get(dropped.id);
          if (timer) {
            clearTimeout(timer);
            timersRef.current.delete(dropped.id);
          }
        }
        return next.slice(0, TOAST_MAX_VISIBLE);
      });
      timersRef.current.set(
        id,
        setTimeout(() => dismiss(id), durationMs),
      );
    },
    [dismiss],
  );

  const contextValue = useMemo(() => ({ notify }), [notify]);

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      <div
        aria-live="polite"
        className="pointer-events-none fixed right-4 top-4 z-[2100] flex w-80 flex-col gap-2"
      >
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role={toast.variant === "error" ? "alert" : "status"}
            className={[
              "pointer-events-auto flex items-start gap-2 rounded-md border border-l-4",
              "border-gray-200 px-3 py-2.5 text-sm shadow-lg",
              VARIANT_CLASS[toast.variant],
            ].join(" ")}
          >
            <div className="min-w-0 flex-1">
              {toast.title ? (
                <div className="font-semibold">{toast.title}</div>
              ) : null}
              <div className="whitespace-pre-line break-words">
                {toast.message}
              </div>
            </div>
            <button
              type="button"
              aria-label="关闭通知"
              onClick={() => dismiss(toast.id)}
              className="shrink-0 rounded p-0.5 text-current/60 hover:bg-black/5"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
                className="h-4 w-4"
              >
                <path d="M6 6l12 12M18 6L6 18" strokeLinecap="round" />
              </svg>
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast 必须在 ToastProvider 内使用");
  }
  return context;
}
