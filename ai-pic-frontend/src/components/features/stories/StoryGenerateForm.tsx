"use client";

import type { VirtualIP } from "@/utils/api/types";
import type { StoryGenerationForm } from "@/utils/storyOptions";
import { CreationOverlay, operatorButtonClass } from "@/components/shared";
import { StoryBasicsSection } from "./StoryBasicsSection";
import { StorySettingSection } from "./StorySettingSection";

interface StoryGenerateFormProps {
  open: boolean;
  onClose: () => void;
  virtualIPs: VirtualIP[];
  generateForm: StoryGenerationForm;
  setGenerateForm: React.Dispatch<React.SetStateAction<StoryGenerationForm>>;
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
      widthClassName="max-w-5xl"
    >
      <form className="space-y-5">
        <StoryBasicsSection
          generateForm={generateForm}
          setGenerateForm={setGenerateForm}
        />

        <StorySettingSection
          virtualIPs={virtualIPs}
          generateForm={generateForm}
          setGenerateForm={setGenerateForm}
          onCharacterToggle={onCharacterToggle}
          onNavigateToVirtualIP={onNavigateToVirtualIP}
        />

        <div>
          <button
            type="button"
            onClick={onPreviewPrompt}
            className={operatorButtonClass("secondary")}
          >
            生成提示词预览
          </button>
          {showPromptPreview && (
            <div className="mt-3 max-h-64 overflow-auto rounded-md border border-gray-200 bg-gray-50 p-3">
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
            className={operatorButtonClass("secondary")}
          >
            取消
          </button>
          <button
            type="button"
            onClick={onSubmit}
            disabled={generating}
            className={operatorButtonClass("primary")}
          >
            {generating ? "生成中..." : useAsync ? "创建异步任务" : "开始生成"}
          </button>
        </div>
      </form>
    </CreationOverlay>
  );
}
