export type NotifyVariant = "success" | "error" | "warning" | "info";

export interface ToastOptions {
  durationMs?: number;
  title?: string;
}

export interface ToastItem {
  id: number;
  message: string;
  variant: NotifyVariant;
  title?: string;
  durationMs: number;
}

export const TOAST_DEFAULT_DURATION_MS: Record<NotifyVariant, number> = {
  success: 5000,
  info: 5000,
  warning: 7000,
  error: 8000,
};

export const TOAST_MAX_VISIBLE = 5;
