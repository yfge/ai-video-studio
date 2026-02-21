"use client";

import type { ReactNode } from "react";
import type { VirtualIP } from "@/utils/api/types";
import { MarketingFields, MultiModelSelector } from "@/components/shared";
import type { EpisodeGenForm } from "@/hooks/useStoryDetail";
import {
  EpisodeContextPackPreview,
  type EpisodeContextPackPreviewProps,
} from "./EpisodeContextPackPreview";

interface EpisodeGeneratePanelProps {
  genOpen: boolean;
  setGenOpen: (open: boolean) => void;
  genForm: EpisodeGenForm;
  setGenForm: React.Dispatch<React.SetStateAction<EpisodeGenForm>>;
  vips: VirtualIP[];
  focusCharacters: number[];
  onToggleFocusCharacter: (id: number, checked: boolean) => void;
  useAsync: boolean;
  setUseAsync: (value: boolean) => void;
  promptPreview: string;
  onPreviewPrompt: () => void;
  onGenerate: () => void;
  canGenerate?: boolean;
  contextPackPreviewProps: EpisodeContextPackPreviewProps;
  readinessPanel?: ReactNode;
}

export function EpisodeGeneratePanel({
  genOpen,
  setGenOpen,
  genForm,
  setGenForm,
  vips,
  focusCharacters,
  onToggleFocusCharacter,
  useAsync,
  setUseAsync,
  promptPreview,
  onPreviewPrompt,
  onGenerate,
  canGenerate = true,
  contextPackPreviewProps,
  readinessPanel,
}: EpisodeGeneratePanelProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">生成剧集</h2>
        <button
          onClick={() => setGenOpen(!genOpen)}
          className="text-blue-600 hover:text-blue-800 text-sm"
        >
          {genOpen ? "收起" : "展开"}
        </button>
      </div>
      {genOpen && (
        <div className="mt-4 space-y-4">
          {/* Readiness check panel */}
          {readinessPanel}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                生成集数
              </label>
              <input
                type="number"
                min={1}
                max={20}
                value={genForm.episode_count}
                onChange={(e) =>
                  setGenForm((prev) => ({
                    ...prev,
                    episode_count: parseInt(e.target.value) || 1,
                  }))
                }
                className="w-full px-3 py-2 border rounded"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                每集时长（分钟）
              </label>
              <input
                type="number"
                min={1}
                max={120}
                value={genForm.episode_duration}
                onChange={(e) =>
                  setGenForm((prev) => ({
                    ...prev,
                    episode_duration: parseInt(e.target.value) || 30,
                  }))
                }
                className="w-full px-3 py-2 border rounded"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                复杂度
              </label>
              <select
                value={genForm.plot_complexity}
                onChange={(e) =>
                  setGenForm((prev) => ({
                    ...prev,
                    plot_complexity: e.target.value,
                  }))
                }
                className="w-full px-3 py-2 border rounded"
              >
                <option value="simple">简单</option>
                <option value="medium">中等</option>
                <option value="complex">复杂</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                节奏
              </label>
              <select
                value={genForm.pacing}
                onChange={(e) =>
                  setGenForm((prev) => ({ ...prev, pacing: e.target.value }))
                }
                className="w-full px-3 py-2 border rounded"
              >
                <option value="slow">慢</option>
                <option value="medium">中</option>
                <option value="fast">快</option>
              </select>
            </div>
            <MultiModelSelector
              label="模型"
              value={genForm.model ? [genForm.model] : []}
              onChange={(ids) =>
                setGenForm((prev) => ({ ...prev, model: ids[0] || "" }))
              }
              modelType="text"
              multiple={false}
              helperText="留空时将由后端推荐最佳模型"
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                温度（{genForm.temperature.toFixed(1)}）
              </label>
              <input
                type="range"
                min={0}
                max={1.5}
                step={0.1}
                value={genForm.temperature}
                onChange={(e) =>
                  setGenForm((prev) => ({
                    ...prev,
                    temperature: parseFloat(e.target.value),
                  }))
                }
                className="w-full"
              />
            </div>
          </div>
          <MarketingFields
            form={genForm}
            setForm={setGenForm}
            title="市场/微类型/节奏模板"
            idPrefix="episode"
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              额外要求
            </label>
            <textarea
              value={genForm.additional_requirements}
              onChange={(e) =>
                setGenForm((prev) => ({
                  ...prev,
                  additional_requirements: e.target.value,
                }))
              }
              rows={2}
              className="w-full px-3 py-2 border rounded"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              聚焦角色（可选）
            </label>
            <div className="flex flex-wrap gap-2">
              {vips.map((v) => (
                <label
                  key={v.id}
                  className={`px-3 py-1 text-xs rounded-full border cursor-pointer ${
                    focusCharacters.includes(v.id)
                      ? "bg-blue-500 text-white border-blue-500"
                      : "bg-white text-gray-700 border-gray-300"
                  }`}
                >
                  <input
                    type="checkbox"
                    className="hidden"
                    checked={focusCharacters.includes(v.id)}
                    onChange={(e) =>
                      onToggleFocusCharacter(v.id, e.target.checked)
                    }
                  />
                  {v.name}
                </label>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-4">
            <label className="text-sm text-gray-700 flex items-center gap-2">
              <input
                type="checkbox"
                checked={useAsync}
                onChange={(e) => setUseAsync(e.target.checked)}
              />{" "}
              异步任务
            </label>
          </div>

          <EpisodeContextPackPreview {...contextPackPreviewProps} />

          <div className="flex gap-2">
            <button
              type="button"
              onClick={onPreviewPrompt}
              className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
            >
              提示词预览
            </button>
            <button
              type="button"
              onClick={onGenerate}
              disabled={!canGenerate}
              className={`px-4 py-2 rounded ${
                canGenerate
                  ? "bg-green-600 text-white hover:bg-green-700"
                  : "bg-gray-300 text-gray-500 cursor-not-allowed"
              }`}
              title={!canGenerate ? "请先修复就绪检查中的严重问题" : undefined}
            >
              开始生成
            </button>
          </div>
          {promptPreview && (
            <div className="mt-3 bg-gray-50 p-3 rounded text-sm whitespace-pre-wrap">
              {promptPreview}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
