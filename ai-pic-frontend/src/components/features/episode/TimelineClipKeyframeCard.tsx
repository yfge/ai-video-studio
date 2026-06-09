"use client";

import { operatorButtonClass } from "@/components/shared";

const CARD_CLASS = "rounded-md border border-gray-200 bg-white p-3";
const CARD_TITLE_CLASS = "text-xs font-semibold text-gray-900";
const CARD_DESCRIPTION_CLASS = "text-[11px] leading-4 text-gray-500";

export function TimelineClipKeyframeCard({
  generating,
  canGenerate,
  onGenerate,
}: {
  generating: boolean;
  canGenerate: boolean;
  onGenerate: () => void;
}) {
  return (
    <section className={CARD_CLASS}>
      <div className="mb-3">
        <div className={CARD_TITLE_CLASS}>首尾帧</div>
        <div className={CARD_DESCRIPTION_CLASS}>
          基于上方故事板/IP/环境参考生成片段首帧和尾帧，供视频生成的首尾帧模式使用。
        </div>
      </div>
      <button
        type="button"
        disabled={!canGenerate}
        className={operatorButtonClass("secondary", "w-full")}
        onClick={onGenerate}
      >
        {generating ? "提交中..." : "生成首尾帧"}
      </button>
    </section>
  );
}
