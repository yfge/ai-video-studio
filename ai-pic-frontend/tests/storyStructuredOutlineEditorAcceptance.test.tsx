import { dom } from "./storyNovelAcceptanceTestDom";
import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render } from "@testing-library/react";
import React, { useState } from "react";

import { StoryStructuredOutlineEditor } from "../src/components/features/stories/StoryStructuredOutlineEditor";
import type {
  StorySeedStructuredChapter,
  StorySeedStructuredOutline,
} from "../src/utils/api/types";

describe("StoryStructuredOutlineEditor acceptance", () => {
  afterEach(() => cleanup());

  it("edits all six chapter fields while keeping title focus", () => {
    let latest = outline([chapter(1)]);
    const utils = render(
      <OutlineHarness
        initial={latest}
        onValue={(value) => {
          latest = value;
        }}
      />,
      { container: dom.window.document.body },
    );

    const title = utils.getByLabelText("标题") as HTMLTextAreaElement;
    title.focus();
    fireEvent.input(title, { target: { value: "重写后的标题" } });
    assert.equal(dom.window.document.activeElement, title);

    fireEvent.input(utils.getByLabelText("情节目标"), {
      target: { value: "找到失踪的航图" },
    });
    fireEvent.input(utils.getByLabelText("关键事件（每行一条）"), {
      target: { value: "发现暗门\n取得航图" },
    });
    fireEvent.input(utils.getByLabelText("角色重点（每行一条）"), {
      target: { value: "褚蓝\n李砚" },
    });
    fireEvent.input(utils.getByLabelText("伏笔（每行一条）"), {
      target: { value: "R-17来源" },
    });
    fireEvent.input(utils.getByLabelText("章末状态"), {
      target: { value: "褚蓝带着航图离开" },
    });

    assert.deepEqual(latest.chapters[0], {
      position: 1,
      title: "重写后的标题",
      goal: "找到失踪的航图",
      key_events: ["发现暗门", "取得航图"],
      character_focus: ["褚蓝", "李砚"],
      open_threads: ["R-17来源"],
      end_state: "褚蓝带着航图离开",
    });
  });

  it("splits a chapter without copying its open thread to both halves", () => {
    let latest = outline([{ ...chapter(1), open_threads: ["R-17来源"] }]);
    const utils = render(
      <OutlineHarness
        initial={latest}
        onValue={(value) => {
          latest = value;
        }}
      />,
      { container: dom.window.document.body },
    );

    fireEvent.click(utils.getByRole("button", { name: "拆分" }));

    assert.equal(latest.chapters.length, 2);
    assert.deepEqual(
      latest.chapters.map(({ open_threads }) => open_threads),
      [["R-17来源"], []],
    );
    assert.deepEqual(
      utils
        .getAllByLabelText("伏笔（每行一条）")
        .map((field) => (field as HTMLTextAreaElement).value),
      ["R-17来源", ""],
    );
  });

  it("renders one bounded progression arc instead of hundreds of chapter cards", () => {
    const chapters = Array.from({ length: 64 }, (_, index) => ({
      ...chapter(index + 1),
      title: `第${index + 1}章标题`,
    }));
    const initial: StorySeedStructuredOutline = {
      ...outline(chapters),
      planning_structure_version: 1,
      progression_arcs: [
        progressionArc("arc-001", 1, 32),
        progressionArc("arc-002", 33, 64),
      ],
    };
    const utils = render(
      <OutlineHarness initial={initial} onValue={() => undefined} />,
      { container: dom.window.document.body },
    );

    assert.equal(utils.getAllByLabelText("标题").length, 32);
    assert.equal(
      (utils.getAllByLabelText("标题")[0] as HTMLTextAreaElement).value,
      "第1章标题",
    );
    fireEvent.change(utils.getByLabelText("当前分卷"), {
      target: { value: "arc-002" },
    });
    assert.equal(
      (utils.getAllByLabelText("标题")[0] as HTMLTextAreaElement).value,
      "第33章标题",
    );
  });
});

function OutlineHarness({
  initial,
  onValue,
}: {
  initial: StorySeedStructuredOutline;
  onValue: (value: StorySeedStructuredOutline) => void;
}) {
  const [value, setValue] = useState(initial);
  onValue(value);
  return <StoryStructuredOutlineEditor outline={value} onChange={setValue} />;
}

function outline(
  chapters: StorySeedStructuredChapter[],
): StorySeedStructuredOutline {
  return {
    status: "draft",
    version: 3,
    thread_schedule_version: 0,
    thread_payoffs: [],
    chapters,
  };
}

function chapter(position: number): StorySeedStructuredChapter {
  return {
    position,
    title: "旧标题",
    goal: "推进冲突",
    key_events: ["事件一", "事件二"],
    character_focus: ["褚蓝"],
    open_threads: [],
    end_state: "进入下一阶段",
  };
}

function progressionArc(arc_id: string, start: number, end: number) {
  return {
    arc_id,
    title: `${start}-${end}章阶段`,
    start_position: start,
    end_position: end,
    narrative_goal: "推进阶段冲突",
    ending_state: "形成新选择",
    growth: {},
    major_entries: [],
    world_scope_changes: [],
    threads: [],
  };
}
