import { dom } from "./storyNovelAcceptanceTestDom";
import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import React from "react";

import { StoryNovelLengthPanel } from "../src/components/features/story-detail/StoryNovelLengthPanel";
import type { StoryNovelCreateRevisionPayload } from "../src/utils/api/types";
import { frontendResponse, story } from "./storyNovelLengthPanelFixtures";

describe("StoryNovelLengthPanel acceptance", () => {
  afterEach(() => cleanup());

  it("covers preset defaults, chapter overrides, bulk actions, clearing, and totals", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async (input) => frontendResponse(input);
    try {
      const utils = render(
        <StoryNovelLengthPanel
          story={story}
          revision={null}
          locked={false}
          busy={false}
          onCreate={async () => true}
          onUpdate={async () => true}
        />,
        { container: dom.window.document.body },
      );

      await waitFor(() =>
        assertTotals(utils.container, "5,000", "4,000–6,000"),
      );
      assert.ok(utils.getByText("默认每章 2000–3000 字符，目标 2500"));
      fireEvent.click(utils.getByText("逐章设置（0 章已覆盖）"));

      changeChapterRange(utils, 0, 3300, 4300, 5300);
      assertTotals(utils.container, "6,800", "5,300–8,300");
      assert.ok(utils.getByText("逐章设置（1 章已覆盖）"));

      fireEvent.click(utils.getAllByRole("button", { name: "使用默认" })[0]);
      assertTotals(utils.container, "5,000", "4,000–6,000");
      assert.ok(utils.getByText("逐章设置（0 章已覆盖）"));

      changeChapterRange(utils, 0, 3300, 4300, 5300);
      fireEvent.click(
        utils.getByRole("button", { name: "仅应用到未覆盖章节" }),
      );
      assert.ok(utils.getByText("逐章设置（2 章已覆盖）"));
      assertTotals(utils.container, "6,800", "5,300–8,300");

      fireEvent.click(utils.getByRole("button", { name: "清除全部单章覆盖" }));
      assert.ok(utils.getByText("逐章设置（0 章已覆盖）"));
      assertTotals(utils.container, "5,000", "4,000–6,000");

      fireEvent.change(utils.getByLabelText("长度预设"), {
        target: { value: "short_serial" },
      });
      assert.ok(utils.getByText("默认每章 1500–3000 字符，目标 2200"));
      assertTotals(utils.container, "4,400", "3,000–6,000");

      fireEvent.click(utils.getByRole("button", { name: "应用到全部章节" }));
      fireEvent.change(utils.getByLabelText("长度预设"), {
        target: { value: "commercial_serial" },
      });
      assertTotals(utils.container, "4,400", "3,000–6,000");
      fireEvent.click(utils.getByRole("button", { name: "清除全部单章覆盖" }));
      assertTotals(utils.container, "5,000", "4,000–6,000");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("submits custom defaults, a per-chapter override, and the model in the API payload", async () => {
    const originalFetch = globalThis.fetch;
    const creates: StoryNovelCreateRevisionPayload[] = [];
    globalThis.fetch = async (input) => frontendResponse(input);
    try {
      const utils = render(
        <StoryNovelLengthPanel
          story={story}
          revision={null}
          locked={false}
          busy={false}
          onCreate={async (payload) => {
            creates.push(payload);
            return true;
          }}
          onUpdate={async () => true}
        />,
        { container: dom.window.document.body },
      );

      await waitFor(() =>
        assert.equal(
          (utils.getByLabelText("长度预设") as HTMLSelectElement).value,
          "commercial_serial",
        ),
      );
      fireEvent.change(utils.getByLabelText("长度预设"), {
        target: { value: "custom" },
      });
      fireEvent.input(utils.getByLabelText("最小字数"), {
        target: { value: "3200" },
      });
      fireEvent.input(utils.getByLabelText("目标字数"), {
        target: { value: "4200" },
      });
      fireEvent.input(utils.getByLabelText("最大字数"), {
        target: { value: "5200" },
      });
      fireEvent.click(utils.getByText("逐章设置（0 章已覆盖）"));
      fireEvent.input(utils.getAllByLabelText("目标")[1], {
        target: { value: "4600" },
      });
      await waitFor(() =>
        assert.equal(
          (utils.getByLabelText("正文生成模型（可选）") as HTMLSelectElement)
            .disabled,
          false,
        ),
      );
      fireEvent.change(utils.getByLabelText("正文生成模型（可选）"), {
        target: { value: "codex:gpt-5.6" },
      });

      assertTotals(utils.container, "8,800", "6,400–10,400");
      fireEvent.click(utils.getByRole("button", { name: "创建新平台版本" }));
      await waitFor(() => assert.equal(creates.length, 1));
      assert.deepEqual(creates[0], {
        style: "prose",
        length_profile_id: "custom",
        custom_length_profile: {
          min_chars: 3200,
          target_chars: 4200,
          max_chars: 5200,
        },
        chapter_length_overrides: {
          "2": {
            min_chars: 3200,
            target_chars: 4600,
            max_chars: 5200,
          },
        },
        model: "codex:gpt-5.6",
        model_policy: {
          planning_model: "codex:gpt-5.6",
          prose_model: "codex:gpt-5.6",
          audit_model: null,
        },
      });
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});

function changeChapterRange(
  utils: ReturnType<typeof render>,
  index: number,
  min: number,
  target: number,
  max: number,
) {
  fireEvent.input(utils.getAllByLabelText("最小")[index], {
    target: { value: String(min) },
  });
  fireEvent.input(utils.getAllByLabelText("目标")[index], {
    target: { value: String(target) },
  });
  fireEvent.input(utils.getAllByLabelText("最大")[index], {
    target: { value: String(max) },
  });
}

function assertTotals(container: HTMLElement, target: string, range: string) {
  const text =
    container.querySelector(".bg-blue-50")?.textContent?.replace(/\s+/g, "") ||
    "";
  assert.ok(text.includes(`预计目标：${target}字`), text);
  assert.ok(text.includes(`允许范围：${range}字`), text);
}
