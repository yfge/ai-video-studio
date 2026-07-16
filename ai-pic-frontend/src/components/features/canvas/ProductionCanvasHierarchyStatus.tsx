import { OperatorPanel, operatorButtonClass } from "@/components/shared";

export function ProductionCanvasHierarchyStatus({
  error,
  hasDomainContext,
  loading,
  onRetry,
}: {
  error: string | null;
  hasDomainContext: boolean;
  loading: boolean;
  onRetry: () => void;
}) {
  if (!hasDomainContext) {
    return (
      <OperatorPanel className="flex h-[420px] flex-col items-center justify-center gap-3 p-6 text-center">
        <div
          aria-label="业务实体层级无限画布"
          className="max-w-md"
          role="region"
        >
          <div className="text-sm font-semibold text-slate-800">
            先输入生产目标
          </div>
          <p className="mt-2 text-xs leading-5 text-slate-500">
            画布会根据 prompt 复用匹配资产；缺失且描述明确的
            IP、环境会自动创建， 这里只展开本次生产相关的业务链路。
          </p>
        </div>
      </OperatorPanel>
    );
  }
  if (loading) {
    return (
      <OperatorPanel className="flex h-[560px] items-center justify-center text-sm text-slate-500">
        正在加载 prompt 相关业务层级…
      </OperatorPanel>
    );
  }
  if (!error) {
    return (
      <OperatorPanel className="flex h-[360px] flex-col items-center justify-center gap-3 p-6 text-center">
        <div className="text-sm font-semibold text-slate-800">
          未找到相关业务链路
        </div>
        <p className="max-w-md text-xs leading-5 text-slate-500">
          请在生产目标中明确已有 Story，或写清需要复用或创建的 IP、环境名称。
        </p>
        <button
          className={operatorButtonClass("secondary")}
          type="button"
          onClick={onRetry}
        >
          重新解析
        </button>
      </OperatorPanel>
    );
  }
  return (
    <OperatorPanel className="flex h-[360px] flex-col items-center justify-center gap-3 p-6 text-center">
      <div className="text-sm font-semibold text-red-700">业务层级加载失败</div>
      <p className="text-xs text-slate-500" role="alert">
        {error}
      </p>
      <button
        className={operatorButtonClass("secondary")}
        type="button"
        onClick={onRetry}
      >
        重新加载
      </button>
    </OperatorPanel>
  );
}
