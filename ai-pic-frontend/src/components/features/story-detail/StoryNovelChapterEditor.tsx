"use client";

import { useEffect, useState } from "react";
import {
  StatusPill,
  operatorButtonClass,
  operatorInputClass,
} from "@/components/shared";
import type { StoryNovelChapter, StoryNovelRevision } from "@/utils/api/types";

interface Props {
  revision: StoryNovelRevision;
  busy: boolean;
  onSave: (
    chapter: StoryNovelChapter,
    patch: Partial<StoryNovelChapter>,
  ) => void;
  onMove: (orderedIds: string[]) => void;
  onRegenerate: (chapter: StoryNovelChapter) => void;
}

function ChapterCard({
  chapter,
  locked,
  busy,
  onSave,
  onMove,
  onRegenerate,
  orderedIds,
}: {
  chapter: StoryNovelChapter;
  locked: boolean;
  busy: boolean;
  onSave: Props["onSave"];
  onMove: Props["onMove"];
  onRegenerate: Props["onRegenerate"];
  orderedIds: string[];
}) {
  const [title, setTitle] = useState(chapter.title);
  const [content, setContent] = useState(chapter.content_text);
  const [summary, setSummary] = useState(chapter.summary || "");
  useEffect(() => {
    setTitle(chapter.title);
    setContent(chapter.content_text);
    setSummary(chapter.summary || "");
  }, [chapter]);
  const move = (offset: number) => {
    const index = orderedIds.indexOf(chapter.business_id);
    const next = index + offset;
    if (next < 0 || next >= orderedIds.length) return;
    const ids = [...orderedIds];
    [ids[index], ids[next]] = [ids[next], ids[index]];
    onMove(ids);
  };
  return (
    <article className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-gray-500">第 {chapter.position} 章</span>
        <StatusPill
          tone={chapter.review_status === "ready" ? "green" : "amber"}
        >
          {chapter.review_status === "ready" ? "就绪" : "待复核"}
        </StatusPill>
        <div className="ml-auto flex gap-2">
          <button
            type="button"
            disabled={locked || busy}
            onClick={() => move(-1)}
            className={operatorButtonClass("secondary")}
          >
            上移
          </button>
          <button
            type="button"
            disabled={locked || busy}
            onClick={() => move(1)}
            className={operatorButtonClass("secondary")}
          >
            下移
          </button>
        </div>
      </div>
      <input
        aria-label={`第${chapter.position}章标题`}
        value={title}
        disabled={locked}
        onChange={(event) => setTitle(event.target.value)}
        className={operatorInputClass("mt-3 w-full")}
      />
      <textarea
        aria-label={`第${chapter.position}章正文`}
        value={content}
        disabled={locked}
        onInput={(event) => setContent(event.currentTarget.value)}
        className={operatorInputClass(
          "mt-3 min-h-64 w-full font-serif leading-7",
        )}
      />
      <textarea
        aria-label={`第${chapter.position}章摘要`}
        value={summary}
        disabled={locked}
        onChange={(event) => setSummary(event.target.value)}
        className={operatorInputClass("mt-3 min-h-20 w-full")}
        placeholder="章节摘要"
      />
      {!locked ? (
        <div className="mt-3 flex gap-2">
          <button
            type="button"
            disabled={busy || !title.trim() || !content.trim()}
            onClick={() =>
              onSave(chapter, { title, content_text: content, summary })
            }
            className={operatorButtonClass("primary")}
          >
            保存章节
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => onRegenerate(chapter)}
            className={operatorButtonClass("secondary")}
          >
            局部重生成
          </button>
        </div>
      ) : null}
    </article>
  );
}

export function StoryNovelChapterEditor(props: Props) {
  const chapters = [...props.revision.chapters].sort(
    (a, b) => a.position - b.position,
  );
  const orderedIds = chapters.map((item) => item.business_id);
  return (
    <div className="space-y-4">
      {chapters.map((chapter) => (
        <ChapterCard
          key={chapter.business_id}
          chapter={chapter}
          locked={props.revision.lifecycle_status !== "draft"}
          busy={props.busy}
          onSave={props.onSave}
          onMove={props.onMove}
          onRegenerate={props.onRegenerate}
          orderedIds={orderedIds}
        />
      ))}
    </div>
  );
}
