"use client";

import { ModelSelector, operatorButtonClass } from "@/components/shared";
import { useState } from "react";

interface Props {
  disabled: boolean;
  onRun: (reviewModel?: string) => void;
}

export function StoryNovelReviewControls({ disabled, onRun }: Props) {
  const [reviewModel, setReviewModel] = useState("codex:gpt-5.6-sol");
  return (
    <>
      <div className="min-w-72 flex-1">
        <ModelSelector
          value={reviewModel}
          onChange={setReviewModel}
          label="全书审读模型"
          helperText="只影响本次连续性与质量审读，不修改已冻结的生成模型策略。"
          autoLabel="使用 Revision 审计模型"
          modelType="text"
          disabled={disabled}
          cacheKey="story-novel-review-models"
        />
      </div>
      <button
        type="button"
        disabled={disabled}
        onClick={() => onRun(reviewModel.trim() || undefined)}
        className={operatorButtonClass("secondary")}
      >
        运行连续性检查
      </button>
    </>
  );
}
