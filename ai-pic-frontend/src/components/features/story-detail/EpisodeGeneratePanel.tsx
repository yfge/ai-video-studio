"use client";

import type { ReactNode } from "react";
import {
  OperatorSectionHeader,
  operatorButtonClass,
} from "@/components/shared";
import type { EpisodeGenForm } from "@/hooks/useStoryDetail";
import {
  EpisodeContextPackPreview,
  type EpisodeContextPackPreviewProps,
} from "./EpisodeContextPackPreview";
import { EpisodeGeneratePanelFields } from "./EpisodeGeneratePanelFields";

interface EpisodeGeneratePanelProps {
  genOpen: boolean;
  setGenOpen: (open: boolean) => void;
  genForm: EpisodeGenForm;
  setGenForm: React.Dispatch<React.SetStateAction<EpisodeGenForm>>;
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
    <div className="space-y-4">
      <OperatorSectionHeader
        title="生成剧集"
        subtitle="继承当前 IP 和故事上下文"
        className="border border-gray-200 bg-white"
        action={
          <button
            type="button"
            onClick={() => setGenOpen(!genOpen)}
            className={operatorButtonClass("ghost")}
          >
            {genOpen ? "收起" : "展开"}
          </button>
        }
      />
      {genOpen && (
        <div className="space-y-4">
          {readinessPanel}

          <EpisodeGeneratePanelFields
            genForm={genForm}
            setGenForm={setGenForm}
          />

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
              className={operatorButtonClass("secondary")}
            >
              提示词预览
            </button>
            <button
              type="button"
              onClick={onGenerate}
              disabled={!canGenerate}
              className={operatorButtonClass("primary")}
              title={!canGenerate ? "请先修复就绪检查中的严重问题" : undefined}
            >
              开始生成
            </button>
          </div>
          {promptPreview && (
            <div className="mt-3 whitespace-pre-wrap rounded-md border border-gray-200 bg-gray-50 p-3 text-xs text-gray-700">
              {promptPreview}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
