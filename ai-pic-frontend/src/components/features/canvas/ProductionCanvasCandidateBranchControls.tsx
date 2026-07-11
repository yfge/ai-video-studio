import { useRef, useState } from "react";
import { operatorButtonClass } from "@/components/shared";

export function ProductionCanvasCandidateBranchControls({
  busy,
  candidateId,
  onBranch,
}: {
  busy: boolean;
  candidateId: number;
  onBranch: (instruction: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const instructionRef = useRef<HTMLTextAreaElement>(null);
  if (!open) {
    return (
      <button
        type="button"
        className={operatorButtonClass("ghost", "h-8 px-2 text-xs")}
        disabled={busy}
        onClick={() => setOpen(true)}
      >
        从此分支
      </button>
    );
  }
  return (
    <div className="mt-2 border-l-2 border-blue-300 bg-blue-50 px-3 py-2">
      <label
        className="block text-xs font-medium text-blue-950"
        htmlFor={`candidate-branch-instruction-${candidateId}`}
      >
        分支指令（可选）
      </label>
      <textarea
        id={`candidate-branch-instruction-${candidateId}`}
        className="mt-1 min-h-16 w-full resize-y border border-blue-200 bg-white px-2 py-1.5 text-xs text-gray-900 outline-none focus:border-blue-500"
        maxLength={1000}
        ref={instructionRef}
      />
      <div className="mt-2 flex justify-end gap-2">
        <button
          type="button"
          className={operatorButtonClass("ghost", "h-7 px-2 text-xs")}
          onClick={() => setOpen(false)}
        >
          取消
        </button>
        <button
          type="button"
          className={operatorButtonClass("primary", "h-7 px-2 text-xs")}
          onClick={() => {
            setOpen(false);
            onBranch(instructionRef.current?.value || "");
          }}
        >
          开始生成
        </button>
      </div>
    </div>
  );
}
