import Link from "next/link";
import { operatorButtonClass } from "@/components/shared";
import { ProductionCanvasRunControls } from "./ProductionCanvasRunControls";
import { ProductionCanvasTemplatePicker } from "./ProductionCanvasTemplatePicker";

export function ProductionCanvasToolbar({
  actionBusy,
  actionStatus,
  activeRunId,
  busy,
  canEdit = true,
  canExecute = true,
  onAddNote,
  onCancelRun,
  onInsertTemplate,
  onReset,
  onRestore,
  onResumeRun,
  onRunIdChange,
  onRunReady,
  onSave,
  runId,
  status,
}: {
  actionBusy?: boolean;
  actionStatus?: string | null;
  activeRunId?: string;
  busy: boolean;
  canEdit?: boolean;
  canExecute?: boolean;
  onAddNote: () => void;
  onCancelRun?: () => void;
  onInsertTemplate: (templateId: string) => void;
  onReset: () => void;
  onRestore: (runId?: string) => void;
  onResumeRun?: () => void;
  onRunIdChange: (value: string) => void;
  onRunReady?: () => void;
  onSave: () => void;
  runId: string;
  status?: string | null;
}) {
  const hasError = /失败|错误|阻塞/.test(actionStatus || status || "");
  return (
    <details
      className="group relative z-40"
      name="production-canvas-popover"
      onKeyDown={(event) => {
        if (event.key === "Escape") event.currentTarget.removeAttribute("open");
      }}
    >
      <summary
        aria-label="运行详情"
        className={operatorButtonClass(
          "secondary",
          "list-none px-3 text-[13px] [&::-webkit-details-marker]:hidden",
        )}
      >
        <span
          className={`mr-2 h-1.5 w-1.5 rounded-full ${
            hasError
              ? "bg-red-500"
              : actionBusy || busy
              ? "animate-pulse bg-blue-500"
              : "bg-emerald-500"
          }`}
          aria-hidden="true"
        />
        运行详情
        {actionStatus || status ? (
          <span
            aria-live="polite"
            className="ml-2 max-w-32 truncate font-normal text-slate-500"
          >
            状态：{actionStatus || status}
          </span>
        ) : null}
      </summary>
      <div className="absolute right-0 top-10 w-[min(760px,calc(100vw-2rem))] rounded-xl border border-slate-200 bg-white p-4 shadow-xl">
        <div className="mb-3 flex items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div>
            <div className="text-sm font-semibold text-slate-950">运行详情</div>
            <p className="mt-1 text-[13px] text-slate-500">
              保存、恢复与后台运行控制
            </p>
          </div>
          <Link href="/tasks" className={operatorButtonClass("ghost")}>
            查看任务
          </Link>
        </div>
        <ProductionCanvasRunControls
          actionBusy={actionBusy}
          actionStatus={actionStatus}
          activeRunId={activeRunId}
          busy={busy}
          canEdit={canEdit}
          canExecute={canExecute}
          onCancel={onCancelRun}
          onResume={onResumeRun}
          runId={runId}
          status={status}
          onRestore={onRestore}
          onRunIdChange={onRunIdChange}
          onRunReady={onRunReady}
          onSave={onSave}
        />
        <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-3">
          <button
            type="button"
            className={operatorButtonClass("secondary")}
            disabled={!canEdit}
            onClick={onAddNote}
          >
            添加便签
          </button>
          <ProductionCanvasTemplatePicker
            disabled={!canEdit}
            onInsert={onInsertTemplate}
          />
          <button
            type="button"
            aria-label="重置"
            className={operatorButtonClass("ghost", "ml-auto")}
            disabled={!canEdit}
            onClick={onReset}
          >
            重置画布
          </button>
        </div>
      </div>
    </details>
  );
}
