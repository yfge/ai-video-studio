import type { ScriptGenerationRequest } from "@/utils/api/types";

interface ScriptProductionPipelineOptionsProps {
  generateForm: ScriptGenerationRequest;
  setGenerateForm: React.Dispatch<
    React.SetStateAction<ScriptGenerationRequest>
  >;
  useAsync: boolean;
}

export function ScriptProductionPipelineOptions({
  generateForm,
  setGenerateForm,
  useAsync,
}: ScriptProductionPipelineOptionsProps) {
  return (
    <div className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="font-medium">生产级异步链路</div>
          <div className="mt-1 text-emerald-700">
            异步生成将执行剧本评分、自动返修，并可继续生成音轨时间轴与分镜占位。
          </div>
        </div>
        <label className="flex items-center gap-2 text-sm font-medium">
          <input
            type="checkbox"
            checked={generateForm.auto_timeline_pipeline ?? true}
            disabled={!useAsync}
            onChange={(e) =>
              setGenerateForm((prev) => ({
                ...prev,
                auto_timeline_pipeline: e.target.checked,
                generation_mode: "production",
              }))
            }
          />
          自动生成时间轴与分镜占位
        </label>
      </div>
    </div>
  );
}
