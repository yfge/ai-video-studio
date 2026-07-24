import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  appendOutlineChapter,
  mergeOutlineChapterWithNext,
  moveOutlineChapter,
  moveOutlinePosition,
  removeOutlineChapter,
  replaceOutlineChapters,
  splitOutlineChapter,
  validateStructuredOutline,
} from "../src/components/features/stories/storyStructuredOutline";
import type {
  StorySeedStructuredChapter,
  StorySeedStructuredOutline,
} from "../src/utils/api/types";

describe("structured Story Seed outline", () => {
  it("adds, reorders, splits, merges, and removes continuous chapters", () => {
    const chapters = [chapter(1, "开端"), chapter(2, "转折")];
    const added = appendOutlineChapter(chapters);
    assert.deepEqual(
      added.map((item) => item.position),
      [1, 2, 3],
    );

    const moved = moveOutlineChapter(added, 2, 0);
    assert.equal(moved[0].title, "第 3 章");
    assert.deepEqual(
      moved.map((item) => item.position),
      [1, 2, 3],
    );

    const split = splitOutlineChapter(chapters, 0);
    assert.equal(split.length, 3);
    assert.deepEqual(
      split.map((item) => item.position),
      [1, 2, 3],
    );
    assert.ok(split[0].key_events.length);
    assert.ok(split[1].key_events.length);

    const merged = mergeOutlineChapterWithNext(split, 0);
    assert.equal(merged.length, 2);
    assert.equal(merged[0].end_state, split[1].end_state);
    assert.deepEqual(
      removeOutlineChapter(merged, 0).map((item) => item.position),
      [1],
    );
  });

  it("validates required fields without imposing a chapter cap", () => {
    const chapters = Array.from({ length: 48 }, (_, index) =>
      chapter(index + 1, `第 ${index + 1} 章`),
    );
    const outline: StorySeedStructuredOutline = {
      status: "draft",
      version: 1,
      thread_schedule_version: 1,
      thread_payoffs: [],
      chapters,
    };
    assert.equal(validateStructuredOutline(outline), null);
    assert.match(
      validateStructuredOutline({
        ...outline,
        chapters: [{ ...chapters[0], key_events: [] }],
      }) || "",
      /关键事件/,
    );
  });

  it("keeps each thread ID in only one half when splitting a chapter", () => {
    const source = {
      ...chapter(1, "开端"),
      open_threads: ["thread-1"],
    };
    const split = splitOutlineChapter([source], 0);
    assert.deepEqual(split[0].open_threads, ["thread-1"]);
    assert.deepEqual(split[1].open_threads, []);
  });

  it("remaps thread payoff positions when chapter order changes", () => {
    assert.deepEqual(
      [1, 2, 3].map((position) => moveOutlinePosition(position, 0, 2)),
      [3, 1, 2],
    );
    assert.deepEqual(
      [1, 2, 3].map((position) => moveOutlinePosition(position, 2, 0)),
      [2, 3, 1],
    );

    const source: StorySeedStructuredOutline = {
      status: "confirmed",
      version: 1,
      thread_schedule_version: 1,
      chapters: [chapter(1, "开端"), chapter(2, "回收")],
      thread_payoffs: [
        {
          thread_id: "线索来源",
          payoff_position: 2,
          evidence_key_event: "关于“线索来源”的最终证据确认：来自旧档案",
        },
      ],
    };
    const replaced = replaceOutlineChapters(
      source,
      source.chapters,
      () => null,
    );
    assert.equal(replaced.status, "draft");
    assert.deepEqual(replaced.thread_payoffs, []);
  });
});

function chapter(position: number, title: string): StorySeedStructuredChapter {
  return {
    position,
    title,
    goal: "推进冲突",
    key_events: ["事件一", "事件二"],
    character_focus: ["主角"],
    open_threads: [],
    end_state: "进入下一阶段",
  };
}
