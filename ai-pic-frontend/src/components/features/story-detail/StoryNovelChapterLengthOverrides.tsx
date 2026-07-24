"use client";

import { operatorButtonClass, operatorInputClass } from "@/components/shared";
import type {
  NovelChapterLengthOverrides,
  NovelLengthRange,
  StorySeedStructuredChapter,
} from "@/utils/api/types";
import { applyRangeToChapters } from "./storyNovelLengthPlan";

interface Props {
  chapters: StorySeedStructuredChapter[];
  defaults: NovelLengthRange;
  overrides: NovelChapterLengthOverrides;
  disabled: boolean;
  onChange: (overrides: NovelChapterLengthOverrides) => void;
}

export function StoryNovelChapterLengthOverrides({
  chapters,
  defaults,
  overrides,
  disabled,
  onChange,
}: Props) {
  const positions = chapters.map((chapter) => chapter.position);
  const setValue = (
    position: number,
    key: keyof NovelLengthRange,
    value: number,
  ) => {
    const id = String(position);
    onChange({
      ...overrides,
      [id]: { ...(overrides[id] || defaults), [key]: value },
    });
  };

  return (
    <details className="rounded-lg border border-gray-200 p-3">
      <summary className="cursor-pointer text-sm font-medium">
        逐章设置（{Object.keys(overrides).length} 章已覆盖）
      </summary>
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          disabled={disabled}
          onClick={() =>
            onChange(applyRangeToChapters(positions, overrides, defaults))
          }
          className={operatorButtonClass("secondary")}
        >
          应用到全部章节
        </button>
        <button
          type="button"
          disabled={disabled}
          onClick={() =>
            onChange(applyRangeToChapters(positions, overrides, defaults, true))
          }
          className={operatorButtonClass("secondary")}
        >
          仅应用到未覆盖章节
        </button>
        <button
          type="button"
          disabled={disabled || !Object.keys(overrides).length}
          onClick={() => onChange({})}
          className={operatorButtonClass("secondary")}
        >
          清除全部单章覆盖
        </button>
      </div>
      <div className="mt-3 space-y-2">
        {chapters.map((chapter) => {
          const current = overrides[String(chapter.position)];
          return (
            <div
              key={chapter.position}
              className="grid gap-2 rounded-md bg-gray-50 p-3 md:grid-cols-[1fr_repeat(3,8rem)_auto]"
            >
              <div className="text-xs">
                <strong>第 {chapter.position} 章</strong>
                <div className="mt-1 text-gray-500">{chapter.title}</div>
              </div>
              {(["min_chars", "target_chars", "max_chars"] as const).map(
                (key) => (
                  <label key={key} className="text-xs text-gray-500">
                    {rangeLabel[key]}
                    <input
                      type="number"
                      min={1}
                      step={1}
                      disabled={disabled}
                      value={(current || defaults)[key]}
                      onChange={(event) =>
                        setValue(
                          chapter.position,
                          key,
                          Number(event.target.value),
                        )
                      }
                      className={operatorInputClass("mt-1 w-full")}
                    />
                  </label>
                ),
              )}
              <button
                type="button"
                disabled={disabled || !current}
                onClick={() => {
                  const next = { ...overrides };
                  delete next[String(chapter.position)];
                  onChange(next);
                }}
                className={operatorButtonClass("secondary", "self-end")}
              >
                使用默认
              </button>
            </div>
          );
        })}
      </div>
    </details>
  );
}

const rangeLabel: Record<keyof NovelLengthRange, string> = {
  min_chars: "最小",
  target_chars: "目标",
  max_chars: "最大",
};
