import type { PointerEvent as ReactPointerEvent } from "react";
import { StatusPill, operatorButtonClass } from "@/components/shared";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { productionCanvasPortContract } from "./productionCanvasPorts";
import { productionCanvasNodeStatusMeta } from "./productionCanvasSkillNodes";
import {
  displayProductionCanvasNodeTitle,
  getNodeHeight,
} from "./productionCanvasViewModel";

export function CanvasNodeCard({
  editable = true,
  executionDisabled,
  executing,
  node,
  onExecuteNode,
  onOutputPortPointerDown,
  selected,
  worldBounds = { minX: 0, minY: 0 },
  onFocusNode,
  onSelect,
  onPointerDown,
}: {
  editable?: boolean;
  executionDisabled?: boolean;
  executing?: boolean;
  node: ProductionCanvasNode;
  onExecuteNode?: (node: ProductionCanvasNode) => void;
  onOutputPortPointerDown?: (
    event: ReactPointerEvent<HTMLButtonElement>,
    nodeId: string,
    portId: string,
  ) => void;
  selected: boolean;
  worldBounds?: { minX: number; minY: number };
  onFocusNode?: (nodeId: string) => void;
  onSelect: (nodeId: string, additive?: boolean) => void;
  onPointerDown: (
    event: ReactPointerEvent<HTMLButtonElement>,
    nodeId: string,
  ) => void;
}) {
  const status = productionCanvasNodeStatusMeta(node);
  const noteClass =
    node.kind === "note"
      ? "border-amber-200 bg-amber-50/95"
      : "border-gray-200 bg-white";
  const canExecute = Boolean(node.skill && node.kind !== "note");
  const executeDisabled = executing || executionDisabled;
  const displayTitle = displayProductionCanvasNodeTitle(node);
  const ports = productionCanvasPortContract(node);

  return (
    <div
      className={`group absolute rounded-xl border shadow-sm transition ${
        selected ? "ring-2 ring-blue-500 ring-offset-2" : "hover:shadow-md"
      } ${noteClass}`}
      style={{
        left: node.x - worldBounds.minX,
        top: node.y - worldBounds.minY,
        width: node.width,
        height: getNodeHeight(node),
      }}
      aria-current={selected ? "true" : undefined}
      data-canvas-node={node.id}
      onDoubleClickCapture={(event) => {
        event.stopPropagation();
        onFocusNode?.(node.id);
      }}
    >
      {ports.inputPorts?.map((port, index) => (
        <button
          key={port.id}
          type="button"
          aria-label={`输入端口 ${port.label} ${port.type}`}
          className={`absolute -left-2 z-10 h-4 w-4 rounded-full border-2 border-white bg-blue-500 shadow-sm transition-opacity ${
            selected
              ? "opacity-100"
              : "opacity-0 group-hover:opacity-100 group-focus-within:opacity-100"
          }`}
          data-canvas-input-port={`${node.id}:${port.id}`}
          style={{ top: 28 + index * 18 }}
          title={`${port.label} · ${port.type}`}
        />
      ))}
      {ports.outputPorts?.map((port, index) => (
        <button
          key={port.id}
          type="button"
          aria-label={`输出端口 ${port.label} ${port.type}`}
          className={`absolute -right-2 z-10 h-4 w-4 rounded-full border-2 border-white bg-emerald-500 shadow-sm transition-opacity ${
            selected
              ? "opacity-100"
              : "opacity-0 group-hover:opacity-100 group-focus-within:opacity-100"
          }`}
          data-canvas-output-port={`${node.id}:${port.id}`}
          style={{ top: 28 + index * 18 }}
          title={`${port.label} · ${port.type}`}
          onPointerDown={(event) =>
            onOutputPortPointerDown?.(event, node.id, port.id)
          }
        />
      ))}
      <button
        type="button"
        className={`h-full w-full rounded-lg p-3 text-left ${
          editable ? "cursor-grab active:cursor-grabbing" : "cursor-default"
        } ${canExecute ? "pb-11" : ""}`}
        aria-label={`${node.label} ${displayTitle}`}
        aria-pressed={selected}
        onClick={(event) => {
          if (event.detail === 0) {
            onSelect(node.id, event.shiftKey || event.metaKey || event.ctrlKey);
          }
          event.currentTarget
            .closest<HTMLElement>("[data-production-canvas='infinite-canvas']")
            ?.focus({ preventScroll: true });
        }}
        onPointerDown={(event) => onPointerDown(event, node.id)}
      >
        <div className="flex items-center justify-between gap-2">
          <div className="truncate text-xs font-semibold text-gray-950">
            {node.label}
          </div>
          <StatusPill tone={status.tone}>{status.label}</StatusPill>
        </div>
        <div className="mt-2 line-clamp-2 text-xs leading-5 text-gray-600">
          {displayTitle}
        </div>
      </button>
      {canExecute ? (
        <button
          type="button"
          className={operatorButtonClass(
            "secondary",
            "absolute bottom-2 left-3 right-3 h-7 justify-center px-2 text-[11px]",
          )}
          aria-label={`${executing ? "执行中" : "后台执行"} ${node.label}`}
          aria-busy={executing || undefined}
          disabled={executeDisabled}
          onClick={(event) => {
            event.preventDefault();
            event.stopPropagation();
            onSelect(node.id);
            onExecuteNode?.(node);
          }}
          onPointerDown={(event) => {
            event.stopPropagation();
          }}
        >
          {executing ? "执行中" : "后台执行"}
        </button>
      ) : null}
    </div>
  );
}
