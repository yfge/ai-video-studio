"use client";

import { MarketingFields, MultiModelSelector } from "@/components/shared";
import { scriptAPI } from "@/utils/api/endpoints";
import type { ScriptGenerationRequest } from "@/utils/api/types";
import { CommercialScriptOptions } from "./CommercialScriptOptions";
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
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h3 className="text-lg font-semibold mb-4">📝 生成剧本</h3>

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
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Model and temperature */}
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
          <label className="text-sm text-gray-700 flex items-center gap-2">
            <input
              type="checkbox"
              checked={useAsync}
              onChange={(e) => setUseAsync(e.target.checked)}
            />{" "}
            异步任务
          </label>
        </div>
      </div>

      {/* Prompt preview */}
      <div className="mb-2">
        <button
          type="button"
          onClick={handlePreviewPrompt}
          className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
        >
          提示词预览
        </button>
      </div>
      {promptPreview && (
        <div className="mt-2 bg-gray-50 p-3 rounded text-sm whitespace-pre-wrap">
          {promptPreview}
        </div>
      )}

      <div className="flex gap-2">
        <button
          onClick={onGenerate}
          disabled={generating}
          className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
        >
          {generating ? "生成中..." : "开始生成"}
        </button>
        <button
          onClick={onCancel}
          className="bg-gray-500 text-white px-6 py-2 rounded-lg hover:bg-gray-600"
        >
          取消
        </button>
      </div>
    </div>
  );
}
