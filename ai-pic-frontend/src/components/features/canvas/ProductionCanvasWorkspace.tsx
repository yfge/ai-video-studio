import { useMemo, useState, type ComponentProps, type ReactNode } from "react";
import {
  operatorButtonClass,
  operatorInputClass,
  operatorSelectClass,
} from "@/components/shared";
import {
  emptyProductionCanvasFilters,
  filterProductionCanvasNodes,
  productionCanvasFilterFacets,
  type ProductionCanvasFilters,
} from "./productionCanvasFilters";
import { ProductionCanvasSurface } from "./ProductionCanvasSurface";
import { ProductionCanvasSelectionToolbar } from "./ProductionCanvasSelectionToolbar";
import type { ProductionCanvasSelectionActions } from "./useProductionCanvasSelectionActions";

type WorkspaceProps = ComponentProps<typeof ProductionCanvasSurface> & {
  selectionActions: ProductionCanvasSelectionActions;
  viewportControls?: ReactNode;
};

export function ProductionCanvasWorkspace(props: WorkspaceProps) {
  const { canEdit, selectionActions, viewportControls, ...surfaceProps } =
    props;
  const [filters, setFilters] = useState(emptyProductionCanvasFilters);
  const nodes = props.canvasState.nodes;
  const facets = useMemo(() => productionCanvasFilterFacets(nodes), [nodes]);
  const visibleNodes = useMemo(
    () => filterProductionCanvasNodes(nodes, filters),
    [filters, nodes],
  );
  const visibleNodeIds = useMemo(
    () => new Set(visibleNodes.map((node) => node.id)),
    [visibleNodes],
  );
  const setFilter = (key: keyof ProductionCanvasFilters, value: string) =>
    setFilters((current) => ({ ...current, [key]: value }));
  const active = Object.values(filters).some(Boolean);

  return (
    <>
      {canEdit ? (
        <ProductionCanvasSelectionToolbar
          actions={selectionActions}
          canvasState={props.canvasState}
        />
      ) : null}
      <div className="relative">
        <details
          className="group absolute left-3 top-3 z-30"
          name="production-canvas-popover"
          onKeyDown={(event) => {
            if (event.key === "Escape")
              event.currentTarget.removeAttribute("open");
          }}
        >
          <summary
            aria-label="节点筛选"
            className={operatorButtonClass(
              active ? "primary" : "secondary",
              "list-none bg-white/95 text-[13px] shadow-sm backdrop-blur [&::-webkit-details-marker]:hidden",
            )}
          >
            筛选 · {visibleNodes.length}/{nodes.length}
          </summary>
          <div className="absolute left-0 top-10 w-[min(720px,calc(100vw-3rem))] rounded-xl border border-slate-200 bg-white p-3 shadow-xl">
            <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-[minmax(180px,1fr)_repeat(4,minmax(112px,0.55fr))]">
              <input
                aria-label="节点搜索"
                className={operatorInputClass("w-full")}
                placeholder="搜索节点"
                type="search"
                value={filters.query}
                onInput={(event) =>
                  setFilter("query", event.currentTarget.value)
                }
              />
              <FilterSelect
                label="场景筛选"
                placeholder="全部场景"
                options={facets.scenes}
                value={filters.scene}
                onChange={(value) => setFilter("scene", value)}
              />
              <FilterSelect
                label="节点类型"
                placeholder="全部类型"
                options={facets.types}
                value={filters.type}
                onChange={(value) => setFilter("type", value)}
              />
              <FilterSelect
                label="节点状态"
                placeholder="全部状态"
                options={facets.statuses}
                value={filters.status}
                onChange={(value) => setFilter("status", value)}
              />
              <FilterSelect
                label="负责人筛选"
                placeholder="全部负责人"
                options={facets.owners}
                value={filters.owner}
                onChange={(value) => setFilter("owner", value)}
              />
            </div>
            <div className="mt-3 flex items-center justify-end gap-2 border-t border-slate-100 pt-3">
              <button
                type="button"
                disabled={!visibleNodes.length}
                className={operatorButtonClass("secondary")}
                onClick={() => props.onFocusNode(visibleNodes[0]?.id)}
              >
                定位首项
              </button>
              <button
                type="button"
                disabled={!active}
                className={operatorButtonClass("ghost")}
                onClick={() => setFilters(emptyProductionCanvasFilters)}
              >
                清除筛选
              </button>
            </div>
          </div>
        </details>
        <ProductionCanvasSurface
          canEdit={canEdit}
          {...surfaceProps}
          visibleNodeIds={visibleNodeIds}
        />
        {viewportControls ? (
          <div className="absolute bottom-3 left-3 z-30">
            {viewportControls}
          </div>
        ) : null}
      </div>
    </>
  );
}

function FilterSelect({
  label,
  onChange,
  options,
  placeholder,
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  options: string[];
  placeholder: string;
  value: string;
}) {
  return (
    <select
      aria-label={label}
      className={operatorSelectClass("w-full")}
      value={value}
      onChange={(event) => onChange(event.target.value)}
    >
      <option value="">{placeholder}</option>
      {options.map((option) => (
        <option key={option} value={option}>
          {option}
        </option>
      ))}
    </select>
  );
}
