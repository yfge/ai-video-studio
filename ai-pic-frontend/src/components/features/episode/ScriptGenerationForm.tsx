"use client";

import {
  MarketingFields,
  MultiModelSelector,
  operatorButtonClass,
  operatorSelectClass,
  operatorTextareaClass,
} from "@/components/shared";
import { scriptAPI } from "@/utils/api/endpoints";
import type { ScriptGenerationRequest } from "@/utils/api/types";
import { ScriptAsyncModeToggle } from "./ScriptAsyncModeToggle";
import { CommercialScriptOptions } from "./CommercialScriptOptions";
import { ScriptProductionPipelineOptions } from "./ScriptProductionPipelineOptions";
import { ShortDramaScriptTemplateSelector } from "./ShortDramaScriptTemplateSelector";
interface ScriptGenerationFormProps {
  generateForm: ScriptGenerationRequest;
  setGenerateForm: React.Dispatch<
    React.SetStateAction<ScriptGenerationRequest>
  >;
  formats: Array<{ value: string; label: string }>;
  languages: Array<{ value: string; label: string }>;
  useAsync: boolean;
  setUseAsync: (value: boolean) => void;
  promptPreview: string;
  setPromptPreview: (value: string) => void;
  generating: boolean;
  onGenerate: () => void;
  onCancel: () => void;
}
export function ScriptGenerationForm({
  generateForm,
  setGenerateForm,
  formats,
  languages,
  useAsync,
  setUseAsync,
  promptPreview,
  setPromptPreview,
  generating,
  onGenerate,
  onCancel,
}: ScriptGenerationFormProps) {
  const handlePreviewPrompt = async () => {
    setPromptPreview("加载中...");
    const res = await scriptAPI.previewScriptPrompt(generateForm);
    if (res.success && res.data) {
      setPromptPreview(res.data.prompt ?? "（空内容）");
    } else {
      setPromptPreview("生成提示词失败");
    }
  };
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-950">生成剧本</h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <CommercialScriptOptions
          generateForm={generateForm}
          setGenerateForm={setGenerateForm}
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            剧本格式
          </label>
          <select
            value={generateForm.format_type}
            onChange={(e) =>
              setGenerateForm((prev) => ({
                ...prev,
                format_type: e.target.value,
              }))
            }
            className={operatorSelectClass("w-full")}
          >
            {formats.map((format) => (
              <option key={format.value} value={format.value}>
                {format.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            语言
          </label>
          <select
            value={generateForm.language}
            onChange={(e) =>
              setGenerateForm((prev) => ({ ...prev, language: e.target.value }))
            }
            className={operatorSelectClass("w-full")}
          >
            {languages.map((language) => (
              <option key={language.value} value={language.value}>
                {language.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            对话风格
          </label>
          <select
            value={generateForm.dialogue_style}
            onChange={(e) =>
              setGenerateForm((prev) => ({
                ...prev,
                dialogue_style: e.target.value,
              }))
            }
            className={operatorSelectClass("w-full")}
          >
            <option value="formal">正式</option>
            <option value="natural">自然</option>
            <option value="casual">随意</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            场景描述详细程度
          </label>
          <select
            value={generateForm.scene_detail_level}
            onChange={(e) =>
              setGenerateForm((prev) => ({
                ...prev,
                scene_detail_level: e.target.value,
              }))
            }
            className={operatorSelectClass("w-full")}
          >
            <option value="minimal">简洁</option>
            <option value="medium">中等</option>
            <option value="detailed">详细</option>
          </select>
        </div>
      </div>

      <MarketingFields
        form={generateForm}
        setForm={setGenerateForm}
        title="市场/微类型/节奏模板"
        idPrefix="script"
      />

      <ShortDramaScriptTemplateSelector setGenerateForm={setGenerateForm} />

      <ScriptProductionPipelineOptions
        generateForm={generateForm}
        setGenerateForm={setGenerateForm}
        useAsync={useAsync}
      />

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          额外要求
        </label>
        <textarea
          value={generateForm.additional_requirements}
          onChange={(e) =>
            setGenerateForm((prev) => ({
              ...prev,
              additional_requirements: e.target.value,
            }))
          }
          placeholder="对剧本生成的特殊要求"
          rows={3}
          className={operatorTextareaClass("w-full")}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-2">
        <MultiModelSelector
          label="模型"
          value={generateForm.model ? [generateForm.model] : []}
          onChange={(ids) =>
            setGenerateForm((prev) => ({ ...prev, model: ids[0] || "" }))
          }
          modelType="text"
          multiple={false}
          helperText="留空将使用后端推荐模型"
          className="md:col-span-1"
        />
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            温度（{(generateForm.temperature ?? 0.7).toFixed(1)}）
          </label>
          <input
            type="range"
            min={0}
            max={1.5}
            step={0.1}
            value={generateForm.temperature ?? 0.7}
            onChange={(e) =>
              setGenerateForm((prev) => ({
                ...prev,
                temperature: parseFloat(e.target.value),
              }))
            }
            className="w-full"
          />
        </div>
        <div className="flex items-end">
          <ScriptAsyncModeToggle
            useAsync={useAsync}
            setUseAsync={setUseAsync}
            setGenerateForm={setGenerateForm}
          />
        </div>
      </div>

      <div className="mb-2">
        <button
          type="button"
          onClick={handlePreviewPrompt}
          className={operatorButtonClass("secondary")}
        >
          提示词预览
        </button>
      </div>
      {promptPreview && (
        <div className="mt-2 whitespace-pre-wrap rounded-md border border-gray-200 bg-gray-50 p-3 text-xs text-gray-700">
          {promptPreview}
        </div>
      )}

      <div className="flex gap-2">
        <button
          onClick={onGenerate}
          disabled={generating}
          className={operatorButtonClass("primary")}
        >
          {generating ? "生成中..." : "开始生成"}
        </button>
        <button
          onClick={onCancel}
          className={operatorButtonClass("secondary")}
        >
          取消
        </button>
      </div>
    </div>
  );
}
