import { useMemo, useState, type ComponentProps } from "react";
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

type WorkspaceProps = ComponentProps<typeof ProductionCanvasSurface>;

export function ProductionCanvasWorkspace(props: WorkspaceProps) {
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
      <div className="flex flex-wrap items-center gap-2 border-b border-gray-200 bg-gray-50 px-4 py-2">
        <input
          aria-label="节点搜索"
          className={operatorInputClass("min-w-48 flex-1")}
          placeholder="搜索节点"
          type="search"
          value={filters.query}
          onInput={(event) => setFilter("query", event.currentTarget.value)}
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
        <span
          className="min-w-14 text-right text-xs text-gray-500"
          aria-live="polite"
        >
          {visibleNodes.length}/{nodes.length}
        </span>
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
      <ProductionCanvasSurface {...props} visibleNodeIds={visibleNodeIds} />
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
      className={operatorSelectClass("max-w-36")}
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
