import type { ScriptGenerationRequest } from "@/utils/api/types";

interface ScriptAsyncModeToggleProps {
  useAsync: boolean;
  setUseAsync: (value: boolean) => void;
  setGenerateForm: React.Dispatch<
    React.SetStateAction<ScriptGenerationRequest>
  >;
}

export function ScriptAsyncModeToggle({
  useAsync,
  setUseAsync,
  setGenerateForm,
}: ScriptAsyncModeToggleProps) {
  return (
    <label className="text-sm text-gray-700 flex items-center gap-2">
      <input
        type="checkbox"
        checked={useAsync}
        onChange={(e) => {
          const nextUseAsync = e.target.checked;
          setUseAsync(nextUseAsync);
          setGenerateForm((prev) => ({
            ...prev,
            generation_mode: nextUseAsync ? "production" : "standard",
            auto_timeline_pipeline: nextUseAsync
              ? (prev.auto_timeline_pipeline ?? true)
              : false,
          }));
        }}
      />{" "}
      异步任务
    </label>
  );
}
