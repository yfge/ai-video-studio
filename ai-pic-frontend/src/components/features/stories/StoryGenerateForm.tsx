"use client";

import type { StoryGenerationRequest, VirtualIP } from "@/utils/api";
import { AIModelType } from "@/utils/api";
import { CreationOverlay, MultiModelSelector } from "@/components/shared";
import { GENRES } from "@/hooks/useStories";
import { CharacterSelector } from "./CharacterSelector";

interface StoryGenerateFormProps {
  open: boolean;
  onClose: () => void;
  virtualIPs: VirtualIP[];
  generateForm: StoryGenerationRequest;
  setGenerateForm: React.Dispatch<React.SetStateAction<StoryGenerationRequest>>;
  promptPreview: string;
  showPromptPreview: boolean;
  useAsync: boolean;
  setUseAsync: (value: boolean) => void;
  generating: boolean;
  onCharacterToggle: (characterId: number) => void;
  onPreviewPrompt: () => void;
  onSubmit: () => void;
  onNavigateToVirtualIP: () => void;
}

export function StoryGenerateForm({
  open,
  onClose,
  virtualIPs,
  generateForm,
  setGenerateForm,
  promptPreview,
  showPromptPreview,
  useAsync,
  setUseAsync,
  generating,
  onCharacterToggle,
  onPreviewPrompt,
  onSubmit,
  onNavigateToVirtualIP,
}: StoryGenerateFormProps) {
  return (
    <CreationOverlay
      open={open}
      title="AI生成故事"
      subtitle="与环境/虚拟IP一致的创建面板，补充角色与设定后提交生成"
      onClose={onClose}
      icon={<span className="text-lg">📚</span>}
      widthClassName="max-w-5xl"
    >
      <form className="space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              故事标题 *
            </label>
            <input
              type="text"
              value={generateForm.title}
              onChange={(e) =>
                setGenerateForm((prev) => ({ ...prev, title: e.target.value }))
              }
              placeholder="输入故事标题"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              故事类型
            </label>
            <select
              value={generateForm.genre}
              onChange={(e) =>
                setGenerateForm((prev) => ({ ...prev, genre: e.target.value }))
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {GENRES.map((genre) => (
                <option key={genre.value} value={genre.value}>
                  {genre.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              故事主题
            </label>
            <input
              type="text"
              value={generateForm.theme}
              onChange={(e) =>
                setGenerateForm((prev) => ({ ...prev, theme: e.target.value }))
              }
              placeholder="例如：友情、成长、冒险"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              目标受众
            </label>
            <input
              type="text"
              value={generateForm.target_audience}
              onChange={(e) =>
                setGenerateForm((prev) => ({
                  ...prev,
                  target_audience: e.target.value,
                }))
              }
              placeholder="例如：青少年、成人、儿童"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              预计总时长（分钟）
            </label>
            <input
              type="number"
              value={generateForm.duration_minutes}
              onChange={(e) =>
                setGenerateForm((prev) => ({
                  ...prev,
                  duration_minutes: parseInt(e.target.value) || 30,
                }))
              }
              min="1"
              max="300"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <MultiModelSelector
            label="选择模型"
            value={generateForm.model ? [generateForm.model] : []}
            onChange={(ids) =>
              setGenerateForm((prev) => ({ ...prev, model: ids[0] || "" }))
            }
            modelType={AIModelType.Text}
            multiple={false}
            helperText="为空将由后端自动挑选最佳提供商与模型（故事生成推荐使用支持 JSON Schema 的模型）"
          />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              温度（0.0 - 1.5）
            </label>
            <input
              type="range"
              min="0"
              max="1.5"
              step="0.1"
              value={generateForm.temperature ?? 0.7}
              onChange={(e) =>
                setGenerateForm((prev) => ({
                  ...prev,
                  temperature: parseFloat(e.target.value),
                }))
              }
              className="w-full"
            />
            <div className="text-sm text-gray-600">
              当前温度：{generateForm.temperature?.toFixed(1)}
            </div>
          </div>
        </div>

        <CharacterSelector
          virtualIPs={virtualIPs}
          selectedIds={generateForm.character_ids}
          onToggle={onCharacterToggle}
          onNavigateToVirtualIP={onNavigateToVirtualIP}
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              时间设定
            </label>
            <input
              type="text"
              value={generateForm.setting_time}
              onChange={(e) =>
                setGenerateForm((prev) => ({
                  ...prev,
                  setting_time: e.target.value,
                }))
              }
              placeholder="例如：现代、古代、未来"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              地点设定
            </label>
            <input
              type="text"
              value={generateForm.setting_location}
              onChange={(e) =>
                setGenerateForm((prev) => ({
                  ...prev,
                  setting_location: e.target.value,
                }))
              }
              placeholder="例如：学校、城市、乡村"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            世界观设定
          </label>
          <textarea
            value={generateForm.world_building}
            onChange={(e) =>
              setGenerateForm((prev) => ({
                ...prev,
                world_building: e.target.value,
              }))
            }
            placeholder="描述故事的世界观和背景设定"
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
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
            placeholder="其他特殊要求或偏好"
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <button
            type="button"
            onClick={onPreviewPrompt}
            className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
          >
            生成提示词预览
          </button>
          {showPromptPreview && (
            <div className="mt-3 p-3 border rounded bg-gray-50 max-h-64 overflow-auto">
              <pre className="whitespace-pre-wrap break-words text-sm font-mono text-gray-800">
                {promptPreview}
              </pre>
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          <input
            id="asyncToggle"
            type="checkbox"
            checked={useAsync}
            onChange={(e) => setUseAsync(e.target.checked)}
            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
          />
          <label htmlFor="asyncToggle" className="text-sm text-gray-700">
            使用异步任务（推荐，支持队列）
          </label>
        </div>

        <div className="flex justify-end gap-3 border-t pt-4">
          <button
            type="button"
            onClick={onClose}
            className="bg-gray-500 text-white px-6 py-2 rounded-lg hover:bg-gray-600"
          >
            取消
          </button>
          <button
            type="button"
            onClick={onSubmit}
            disabled={generating}
            className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            {generating
              ? "生成中..."
              : useAsync
                ? "创建异步任务"
                : "开始生成"}
          </button>
        </div>
      </form>
    </CreationOverlay>
  );
}
