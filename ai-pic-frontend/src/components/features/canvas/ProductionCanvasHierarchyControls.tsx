import {
  OperatorSectionHeader,
  operatorButtonClass,
} from "@/components/shared";

export function ProductionCanvasHierarchyControls({
  onRefresh,
  onShowReferencesChange,
  showReferences,
}: {
  onRefresh: () => void;
  onShowReferencesChange: (value: boolean) => void;
  showReferences: boolean;
}) {
  return (
    <>
      <OperatorSectionHeader
        title="业务实体层级"
        subtitle="系列：IP → 故事 → 剧集；单条视频：视频项目 → 主视频 → Timeline 分镜 → 当前视频"
        action={
          <button
            className={operatorButtonClass("ghost")}
            type="button"
            onClick={onRefresh}
          >
            刷新层级
          </button>
        }
      />
      <div className="flex flex-wrap items-center gap-3 border-b border-slate-200 bg-white px-4 py-2 text-[11px] text-slate-500">
        <span>实线：资源 / 参与 / 包含</span>
        <span>箭头：Timeline 生产关系</span>
        <label className="ml-auto inline-flex items-center gap-2 text-slate-600">
          <input
            checked={showReferences}
            type="checkbox"
            onChange={(event) => onShowReferencesChange(event.target.checked)}
          />
          显示环境引用（虚线）
        </label>
      </div>
    </>
  );
}
