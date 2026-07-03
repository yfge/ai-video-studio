import { useEffect, useState } from "react";
import { operatorButtonClass } from "@/components/shared";

export function ProductionCanvasRunControls({
  busy,
  onRestore,
  onRunIdChange,
  onSave,
  runId,
  status,
}: {
  busy: boolean;
  onRestore: (runId?: string) => void;
  onRunIdChange: (value: string) => void;
  onSave: () => void;
  runId: string;
  status?: string | null;
}) {
  const [copyStatus, setCopyStatus] = useState<string | null>(null);
  const trimmedRunId = runId.trim();
  useEffect(() => setCopyStatus(null), [runId]);
  const writeClipboardText = async (text: string) => {
    if (navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(text);
        return;
      } catch {
        // Fall through to the DOM copy path for restricted browser contexts.
      }
    }
    if (typeof document.execCommand !== "function") {
      throw new Error("clipboard copy unavailable");
    }
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    const copied = document.execCommand("copy");
    textarea.remove();
    if (!copied) {
      throw new Error("clipboard copy failed");
    }
  };
  const returnFocusToCanvas = () => {
    document
      .querySelector<HTMLElement>('[data-production-canvas="infinite-canvas"]')
      ?.focus({ preventScroll: true });
  };
  const copyRunId = async () => {
    if (!trimmedRunId) return;
    try {
      await writeClipboardText(trimmedRunId);
      setCopyStatus("已复制 Run ID");
    } catch {
      setCopyStatus("复制失败");
    } finally {
      returnFocusToCanvas();
    }
  };
  const copyRunLink = async () => {
    if (!trimmedRunId) return;
    const url = new URL("/canvas", window.location.origin);
    url.searchParams.set("run_id", trimmedRunId);
    const link = url.toString();
    try {
      await writeClipboardText(link);
      setCopyStatus("已复制链接");
    } catch {
      setCopyStatus(`复制失败，链接已生成：${link}`);
    } finally {
      returnFocusToCanvas();
    }
  };
  const statusText = [status, copyStatus].filter(Boolean).join(" · ");

  return (
    <div className="flex flex-wrap items-end gap-2">
      <label className="min-w-40">
        <span className="text-[11px] font-semibold text-gray-600">Run ID</span>
        <input
          aria-label="Run ID"
          className="mt-1 h-8 w-full rounded-md border border-gray-200 bg-white px-2 text-xs text-gray-800 placeholder:text-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
          value={runId}
          placeholder="创建后自动填入"
          disabled={busy}
          onChange={(event) => onRunIdChange(event.currentTarget.value)}
          onKeyUp={(event) => {
            if (event.key === "Enter" && !busy)
              onRestore(event.currentTarget.value || runId);
          }}
        />
      </label>
      <button
        type="button"
        aria-busy={busy || undefined}
        className={operatorButtonClass("secondary")}
        disabled={busy}
        onClick={onSave}
      >
        保存画布
      </button>
      <button
        type="button"
        aria-busy={busy || undefined}
        className={operatorButtonClass("ghost")}
        disabled={busy}
        onClick={() => onRestore()}
      >
        恢复画布
      </button>
      <button
        type="button"
        className={operatorButtonClass("ghost")}
        disabled={busy || !trimmedRunId}
        onClick={() => void copyRunId()}
      >
        复制 Run ID
      </button>
      <button
        type="button"
        className={operatorButtonClass("ghost")}
        disabled={busy || !trimmedRunId}
        onClick={() => void copyRunLink()}
      >
        复制链接
      </button>
      {statusText ? (
        <div
          className="min-h-8 break-all px-1 py-1 text-xs leading-5 text-gray-500"
          aria-live="polite"
          role="status"
        >
          {status ? <span>{status}</span> : null}
          {status && copyStatus ? <span aria-hidden="true"> · </span> : null}
          {copyStatus ? <span>{copyStatus}</span> : null}
        </div>
      ) : null}
    </div>
  );
}
