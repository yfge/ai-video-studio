import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render } from "@testing-library/react";
import { JSDOM } from "jsdom";
import React from "react";
import { validateStructuredOutline } from "../src/components/features/stories/storyStructuredOutline";
import { StoryStructuredOutlineEditor } from "../src/components/features/stories/StoryStructuredOutlineEditor";
import { StoryThreadPayoffEditor } from "../src/components/features/stories/StoryThreadPayoffEditor";
import type { StorySeedStructuredOutline } from "../src/utils/api/types";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;

const outline = (
  patch: Partial<StorySeedStructuredOutline> = {},
): StorySeedStructuredOutline => ({
  status: "draft",
  version: 1,
  thread_schedule_version: 1,
  chapters: [
    {
      position: 1,
      title: "打开",
      goal: "发现线索",
      key_events: ["发现钥匙"],
      character_focus: [],
      open_threads: ["thread-key"],
      end_state: "保管钥匙",
    },
    {
      position: 2,
      title: "回收",
      goal: "打开密室",
      key_events: ["钥匙打开密室，失踪者留下的账本随之曝光"],
      character_focus: [],
      open_threads: [],
      end_state: "秘密公开",
    },
  ],
  thread_payoffs: [
    {
      thread_id: "thread-key",
      payoff_position: 2,
      evidence_key_event: "钥匙打开密室，失踪者留下的账本随之曝光",
    },
  ],
  ...patch,
});

describe("StorySeed v1 thread payoff contract", () => {
  afterEach(() => cleanup());

  it("accepts one exact later payoff and rejects legacy v0", () => {
    assert.equal(validateStructuredOutline(outline()), null);
    assert.match(
      validateStructuredOutline(
        outline({ thread_schedule_version: 0, thread_payoffs: [] }),
      ) ?? "",
      /v0.*重新结构化/,
    );
    const noThreads = outline({
      thread_schedule_version: 0,
      thread_payoffs: [],
    });
    noThreads.chapters[0].open_threads = [];
    assert.equal(validateStructuredOutline(noThreads), null);
  });

  it("rejects duplicate openings, unknown, duplicate, early, and omitted payoffs", () => {
    const compound = outline();
    compound.chapters[0].open_threads = ["观测员下落；云井审计编号"];
    compound.thread_payoffs[0].thread_id = "观测员下落；云井审计编号";
    assert.match(validateStructuredOutline(compound) ?? "", /原子问题/);
    const duplicateOpening = outline();
    duplicateOpening.chapters[1].open_threads = ["thread-key"];
    assert.match(validateStructuredOutline(duplicateOpening) ?? "", /全书重复/);
    assert.match(
      validateStructuredOutline(
        outline({
          thread_payoffs: [
            {
              thread_id: "unknown",
              payoff_position: 2,
              evidence_key_event: "钥匙打开密室",
            },
          ],
        }),
      ) ?? "",
      /未知伏笔/,
    );
    assert.match(
      validateStructuredOutline(
        outline({
          thread_payoffs: [
            ...outline().thread_payoffs!,
            ...outline().thread_payoffs!,
          ],
        }),
      ) ?? "",
      /重复回收/,
    );
    assert.match(
      validateStructuredOutline(
        outline({
          thread_payoffs: [
            {
              thread_id: "thread-key",
              payoff_position: 1,
              evidence_key_event: "发现钥匙",
            },
          ],
        }),
      ) ?? "",
      /必须在第 1 章之后/,
    );
    assert.match(
      validateStructuredOutline(outline({ thread_payoffs: [] })) ?? "",
      /合同遗漏/,
    );
  });

  it("accepts neutral exact target evidence and limits three payoffs per chapter", () => {
    assert.match(
      validateStructuredOutline(
        outline({
          thread_payoffs: [
            {
              thread_id: "thread-key",
              payoff_position: 2,
              evidence_key_event: "近义改写",
            },
          ],
        }),
      ) ?? "",
      /必须逐字属于/,
    );
    const neutral = outline();
    neutral.chapters[1].key_events = ["钥匙打开密室"];
    neutral.thread_payoffs![0].evidence_key_event = "钥匙打开密室";
    assert.equal(validateStructuredOutline(neutral), null);
    const crowded = outline();
    crowded.chapters[0].open_threads = ["t1", "t2", "t3", "t4"];
    crowded.chapters[1].key_events = crowded.chapters[0].open_threads.map(
      (threadId) => `${threadId} 对应的密室证词公开`,
    );
    crowded.thread_payoffs = crowded.chapters[0].open_threads.map(
      (thread_id) => ({
        thread_id,
        payoff_position: 2,
        evidence_key_event: `${thread_id} 对应的密室证词公开`,
      }),
    );
    assert.match(validateStructuredOutline(crowded) ?? "", /最多回收 3 条/);
  });
});

describe("StorySeed thread payoff editor", () => {
  afterEach(() => cleanup());

  it("edits all three payoff fields and deletes a row", () => {
    const value = outline();
    value.chapters[0].open_threads.push("thread-door");
    value.chapters[1].key_events.push("密室证词公开");
    let changed = value.thread_payoffs;
    const utils = render(
      React.createElement(StoryThreadPayoffEditor, {
        chapters: value.chapters,
        payoffs: value.thread_payoffs,
        disabled: false,
        onChange: (payoffs) => {
          changed = payoffs;
        },
      }),
      { container: dom.window.document.body },
    );
    fireEvent.change(utils.getByLabelText("第 1 条伏笔 ID"), {
      target: { value: "thread-door" },
    });
    assert.equal(changed[0].thread_id, "thread-door");
    fireEvent.change(utils.getByLabelText("第 1 条回收章节"), {
      target: { value: "1" },
    });
    assert.equal(changed[0].payoff_position, 1);
    assert.equal(changed[0].evidence_key_event, "发现钥匙");
    fireEvent.change(utils.getByLabelText("第 1 条关键事件证据"), {
      target: { value: "密室证词公开" },
    });
    assert.equal(changed[0].evidence_key_event, "密室证词公开");
    fireEvent.click(utils.getByRole("button", { name: "删除" }));
    assert.deepEqual(changed, []);
  });

  it("shows legacy v0 as requiring restructure and locks the payoff table", () => {
    const value = outline({ thread_schedule_version: 0, thread_payoffs: [] });
    const utils = render(
      React.createElement(StoryStructuredOutlineEditor, {
        outline: value,
        onChange: () => undefined,
      }),
      { container: dom.window.document.body },
    );
    assert.ok(utils.getByText(/旧版 v0 大纲/));
    assert.equal(
      utils.getByRole("button", { name: "增加回收" }).hasAttribute("disabled"),
      true,
    );
  });
});
