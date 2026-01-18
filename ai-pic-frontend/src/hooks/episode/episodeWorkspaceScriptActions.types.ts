export type ShowAlert = (options: {
  message: string;
  variant: "info" | "success" | "warning" | "error";
  title?: string;
  confirmText?: string;
  onConfirm?: () => void;
}) => void;

export type PendingRegenerateState = {
  taskId: number;
  knownScriptIds: number[];
  createdAtMs: number;
};

export const parsePendingRegenerateState = (raw: string | null) => {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as PendingRegenerateState;
    if (
      typeof parsed?.taskId !== "number" ||
      !Array.isArray(parsed?.knownScriptIds) ||
      typeof parsed?.createdAtMs !== "number"
    ) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
};

