import { operatorButtonClass } from "@/components/shared";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { isManualProductionCanvasNote } from "./productionCanvasSkillNodes";

export function ProductionCanvasNoteControls({
  node,
  onDuplicateNote,
  onUpdateNode,
}: {
  node?: ProductionCanvasNode;
  onDuplicateNote: (nodeId: string) => void;
  onUpdateNode: (nodeId: string, patch: Partial<ProductionCanvasNode>) => void;
}) {
  if (!isManualProductionCanvasNote(node)) return null;

  return (
    <div className="border-t border-gray-100 pt-3">
      <div className="text-xs font-semibold text-gray-700">便签编辑</div>
      <div className="mt-2 grid gap-2">
        <label>
          <span className="text-[11px] font-semibold text-gray-600">
            便签标题
          </span>
          <input
            aria-label="便签标题"
            className="mt-1 h-8 w-full rounded-md border border-gray-200 bg-white px-2 text-xs text-gray-800 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
            value={node.title}
            onInput={(event) =>
              onUpdateNode(node.id, { title: event.currentTarget.value })
            }
          />
        </label>
        <label>
          <span className="text-[11px] font-semibold text-gray-600">
            便签内容
          </span>
          <textarea
            aria-label="便签内容"
            className="mt-1 min-h-20 w-full resize-y rounded-md border border-gray-200 bg-white px-2 py-1.5 text-xs text-gray-800 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
            value={node.detail || ""}
            onInput={(event) =>
              onUpdateNode(node.id, { detail: event.currentTarget.value })
            }
          />
        </label>
        <button
          type="button"
          className={operatorButtonClass("secondary", "justify-center")}
          onClick={() => onDuplicateNote(node.id)}
        >
          复制便签
        </button>
      </div>
    </div>
  );
}
