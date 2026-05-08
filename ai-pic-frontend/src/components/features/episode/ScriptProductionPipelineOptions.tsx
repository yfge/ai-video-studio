import type { ScriptGenerationRequest } from "@/utils/api/types";
import { OperatorState } from "@/components/shared";

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
    <div className="mb-4">
      <OperatorState
        title="生产级异步链路"
        detail="异步生成将执行剧本评分、自动返修，并可继续生成音轨时间轴与分镜占位。"
        action={
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
        }
      />
    </div>
  );
}
