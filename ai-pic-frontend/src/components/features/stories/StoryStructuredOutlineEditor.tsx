"use client";

import { useState, type DragEvent } from "react";
import { operatorButtonClass } from "@/components/shared";
import type {
  StorySeedStructuredChapter,
  StorySeedStructuredOutline,
} from "@/utils/api/types";
import {
  appendOutlineChapter,
  mergeOutlineChapterWithNext,
  moveOutlineChapter,
  moveOutlinePosition,
  removeOutlineChapter,
  replaceOutlineChapters,
  splitOutlineChapter,
  validateStructuredOutline,
} from "./storyStructuredOutline";
import {
  StoryOutlineAction,
  StoryOutlineField,
  StoryOutlineListField,
} from "./StoryStructuredOutlineFields";
import { StoryThreadPayoffEditor } from "./StoryThreadPayoffEditor";

interface Props {
  outline: StorySeedStructuredOutline;
  disabled?: boolean;
  onChange: (outline: StorySeedStructuredOutline) => void;
}

export function StoryStructuredOutlineEditor({
  outline,
  disabled = false,
  onChange,
}: Props) {
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const setChapters = (
    chapters: StorySeedStructuredChapter[],
    mapPayoff?: Parameters<typeof replaceOutlineChapters>[2],
  ) => onChange(replaceOutlineChapters(outline, chapters, mapPayoff));
  const moveChapters = (from: number, to: number) =>
    setChapters(moveOutlineChapter(outline.chapters, from, to), (payoff) =>
      moveOutlinePosition(payoff.payoff_position, from, to),
    );
  const patchChapter = (
    index: number,
    patch: Partial<StorySeedStructuredChapter>,
  ) =>
    setChapters(
      outline.chapters.map((chapter, row) =>
        row === index ? { ...chapter, ...patch } : chapter,
      ),
    );
  const drop = (event: DragEvent<HTMLElement>, to: number) => {
    event.preventDefault();
    const raw = event.dataTransfer.getData("text/plain");
    const from = dragIndex ?? Number(raw);
    if (Number.isInteger(from)) {
      moveChapters(from, to);
    }
    setDragIndex(null);
  };
  const validation = validateStructuredOutline(outline);

  return (
    <section className="space-y-3" aria-label="结构化章节大纲">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-semibold">
          结构化章节计划 · {outline.chapters.length} 章
        </span>
        <span className="text-xs text-gray-500">计划 v{outline.version}</span>
        <span className="text-xs text-gray-500">
          回收合同 v{outline.thread_schedule_version ?? 0}
        </span>
        {validation ? (
          <span role="alert" className="text-xs text-red-600">
            {validation}
          </span>
        ) : null}
      </div>
      {outline.chapters.map((chapter, index) => (
        <article
          key={chapter.position}
          onDragOver={(event) => event.preventDefault()}
          onDrop={(event) => drop(event, index)}
          className="rounded-lg border border-gray-200 bg-gray-50 p-4"
        >
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium text-gray-600">
              第 {chapter.position} 章
            </span>
            <span
              draggable={!disabled}
              onDragStart={(event) => {
                setDragIndex(index);
                event.dataTransfer.setData("text/plain", String(index));
              }}
              onDragEnd={() => setDragIndex(null)}
              className="cursor-grab rounded border border-gray-200 bg-white px-2 py-1 text-xs text-gray-500"
            >
              拖动排序
            </span>
            <div className="ml-auto flex flex-wrap gap-1">
              <StoryOutlineAction
                label="上移"
                disabled={disabled || index === 0}
                onClick={() => moveChapters(index, index - 1)}
              />
              <StoryOutlineAction
                label="下移"
                disabled={disabled || index === outline.chapters.length - 1}
                onClick={() => moveChapters(index, index + 1)}
              />
              <StoryOutlineAction
                label="拆分"
                disabled={disabled}
                onClick={() => {
                  const chapters = splitOutlineChapter(outline.chapters, index);
                  const position = index + 1;
                  const secondEvents = chapters[index + 1].key_events;
                  setChapters(chapters, (payoff) => {
                    if (payoff.payoff_position < position) {
                      return payoff.payoff_position;
                    }
                    if (payoff.payoff_position === position) {
                      return secondEvents.includes(payoff.evidence_key_event)
                        ? position + 1
                        : position;
                    }
                    return payoff.payoff_position + 1;
                  });
                }}
              />
              <StoryOutlineAction
                label="与下一章合并"
                disabled={disabled || index === outline.chapters.length - 1}
                onClick={() => {
                  const position = index + 1;
                  setChapters(
                    mergeOutlineChapterWithNext(outline.chapters, index),
                    (payoff) =>
                      payoff.payoff_position <= position + 1
                        ? Math.min(payoff.payoff_position, position)
                        : payoff.payoff_position - 1,
                  );
                }}
              />
              <StoryOutlineAction
                label="删除"
                disabled={disabled || outline.chapters.length === 1}
                onClick={() => {
                  const removed = outline.chapters[index];
                  setChapters(
                    removeOutlineChapter(outline.chapters, index),
                    (payoff) => {
                      if (
                        removed.open_threads.includes(payoff.thread_id) ||
                        payoff.payoff_position === removed.position
                      ) {
                        return null;
                      }
                      return payoff.payoff_position > removed.position
                        ? payoff.payoff_position - 1
                        : payoff.payoff_position;
                    },
                  );
                }}
              />
            </div>
          </div>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <StoryOutlineField
              label="标题"
              value={chapter.title}
              disabled={disabled}
              onChange={(title) => patchChapter(index, { title })}
            />
            <StoryOutlineField
              label="情节目标"
              value={chapter.goal}
              disabled={disabled}
              onChange={(goal) => patchChapter(index, { goal })}
            />
            <StoryOutlineListField
              label="关键事件（每行一条）"
              values={chapter.key_events}
              disabled={disabled}
              onChange={(key_events) => patchChapter(index, { key_events })}
            />
            <StoryOutlineListField
              label="角色重点（每行一条）"
              values={chapter.character_focus}
              disabled={disabled}
              onChange={(character_focus) =>
                patchChapter(index, { character_focus })
              }
            />
            <StoryOutlineListField
              label="伏笔（每行一条）"
              values={chapter.open_threads}
              disabled={disabled}
              onChange={(open_threads) => patchChapter(index, { open_threads })}
            />
            <StoryOutlineField
              label="章末状态"
              value={chapter.end_state}
              disabled={disabled}
              onChange={(end_state) => patchChapter(index, { end_state })}
            />
          </div>
        </article>
      ))}
      {outline.thread_schedule_version !== 1 &&
      outline.chapters.some((chapter) => chapter.open_threads.length) ? (
        <p className="text-xs text-amber-700">
          这是旧版 v0 大纲，需重新运行结构化生成后才能确认。
        </p>
      ) : null}
      <StoryThreadPayoffEditor
        chapters={outline.chapters}
        payoffs={outline.thread_payoffs ?? []}
        disabled={disabled || outline.thread_schedule_version !== 1}
        onChange={(thread_payoffs) =>
          onChange({ ...outline, status: "draft", thread_payoffs })
        }
      />
      <button
        type="button"
        disabled={disabled}
        onClick={() => setChapters(appendOutlineChapter(outline.chapters))}
        className={operatorButtonClass("secondary")}
      >
        增加章节
      </button>
    </section>
  );
}
