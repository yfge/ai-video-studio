import { dom } from "./storyNovelAcceptanceTestDom";
import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import React from "react";

import { StoryNovelLengthPanel } from "../src/components/features/story-detail/StoryNovelLengthPanel";
import type {
  Story,
  StoryNovelCreateRevisionPayload,
} from "../src/utils/api/types";

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
        assertTotals(utils.container, "8,000", "6,000–10,000"),
      );
      assert.ok(utils.getByText("默认每章 3000–5000 字符，目标 4000"));
      fireEvent.click(utils.getByText("逐章设置（0 章已覆盖）"));

      changeChapterRange(utils, 0, 3300, 4300, 5300);
      assertTotals(utils.container, "8,300", "6,300–10,300");
      assert.ok(utils.getByText("逐章设置（1 章已覆盖）"));

      fireEvent.click(utils.getAllByRole("button", { name: "使用默认" })[0]);
      assertTotals(utils.container, "8,000", "6,000–10,000");
      assert.ok(utils.getByText("逐章设置（0 章已覆盖）"));

      changeChapterRange(utils, 0, 3300, 4300, 5300);
      fireEvent.click(
        utils.getByRole("button", { name: "仅应用到未覆盖章节" }),
      );
      assert.ok(utils.getByText("逐章设置（2 章已覆盖）"));
      assertTotals(utils.container, "8,300", "6,300–10,300");

      fireEvent.click(utils.getByRole("button", { name: "清除全部单章覆盖" }));
      assert.ok(utils.getByText("逐章设置（0 章已覆盖）"));
      assertTotals(utils.container, "8,000", "6,000–10,000");

      fireEvent.change(utils.getByLabelText("长度预设"), {
        target: { value: "short_serial" },
      });
      assert.ok(utils.getByText("默认每章 1500–3000 字符，目标 2200"));
      assertTotals(utils.container, "4,400", "3,000–6,000");

      fireEvent.click(utils.getByRole("button", { name: "应用到全部章节" }));
      fireEvent.change(utils.getByLabelText("长度预设"), {
        target: { value: "standard_serial" },
      });
      assertTotals(utils.container, "4,400", "3,000–6,000");
      fireEvent.click(utils.getByRole("button", { name: "清除全部单章覆盖" }));
      assertTotals(utils.container, "8,000", "6,000–10,000");
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
          "standard_serial",
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

function profileResponse() {
  return new Response(
    JSON.stringify({
      success: true,
      data: {
        items: [
          {
            profile_id: "standard_serial",
            name: "标准连载",
            min_chars: 3000,
            target_chars: 4000,
            max_chars: 5000,
          },
          {
            profile_id: "short_serial",
            name: "短章连载",
            min_chars: 1500,
            target_chars: 2200,
            max_chars: 3000,
          },
        ],
      },
    }),
    { headers: { "content-type": "application/json" } },
  );
}

function frontendResponse(input: string | URL | Request) {
  return String(input).includes("/ai/models/available")
    ? new Response(
        JSON.stringify({
          success: true,
          data: {
            models: [
              {
                model_id: "codex:gpt-5.6",
                id: "gpt-5.6",
                name: "GPT-5.6",
                provider: "codex",
                type: "text_generation",
                capabilities: ["text_generation"],
              },
            ],
          },
        }),
        { headers: { "content-type": "application/json" } },
      )
    : profileResponse();
}

const story = {
  id: 1,
  business_id: "story-business-id",
  story_seed_status: "confirmed",
  story_seed: {
    schema: "story_seed_v2",
    structured_outline: {
      status: "confirmed",
      version: 7,
      thread_schedule_version: 1,
      thread_payoffs: [],
      chapters: [
        {
          position: 1,
          title: "第一章",
          goal: "发现线索",
          key_events: ["发现红尘"],
          character_focus: ["褚蓝"],
          open_threads: [],
          end_state: "保存样本",
        },
        {
          position: 2,
          title: "第二章",
          goal: "追查来源",
          key_events: ["检查暗渠"],
          character_focus: ["褚蓝"],
          open_threads: [],
          end_state: "锁定入口",
        },
      ],
    },
  },
} as Story;
