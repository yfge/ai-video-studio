import { dom } from "./storyNovelAcceptanceTestDom";
import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { act, cleanup, render, waitFor } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";
import React from "react";

import { StoryNovelGenerationStatus } from "../src/components/features/story-detail/StoryNovelGenerationStatus";
import { StoryNovelWorkflowPanel } from "../src/components/features/story-detail/StoryNovelWorkflowPanel";
import {
  completedRevision,
  pendingRevision,
  story,
} from "./storyNovelGenerationPollingFixtures";

describe("StoryNovelWorkflow generation polling acceptance", () => {
  afterEach(() => cleanup());

  it("lists body and extraction status for every planned chapter", () => {
    const html = renderToStaticMarkup(
      <StoryNovelGenerationStatus revision={pendingRevision} />,
    );

    assert.match(html, /aria-label="逐章生成进度"/);
    assert.match(html, /第 1 章 第一章 · 正文 body_ready · 提取 blocked/);
    assert.match(html, /第 2 章 第二章 · 正文 pending · 提取 pending/);
  });

  it("freezes edits while running, polls chapter body/extraction state, and unlocks on terminal status", async () => {
    const originalFetch = globalThis.fetch;
    const originalSetInterval = dom.window.setInterval;
    const originalClearInterval = dom.window.clearInterval;
    let intervalRefresh: (() => Promise<void>) | null = null;
    let taskCalls = 0;
    const taskLocks: boolean[] = [];

    dom.window.setInterval = ((handler: TimerHandler) => {
      intervalRefresh = handler as () => Promise<void>;
      return 71;
    }) as typeof dom.window.setInterval;
    dom.window.clearInterval = (() =>
      undefined) as typeof dom.window.clearInterval;
    globalThis.fetch = async (input) => {
      const url = String(input);
      if (url.endsWith("/api/v1/novel/length-profiles")) {
        return response({
          items: [
            {
              profile_id: "standard_serial",
              name: "标准连载",
              min_chars: 3000,
              target_chars: 4000,
              max_chars: 5000,
            },
          ],
        });
      }
      if (url.includes("/api/v1/ai/models/available")) {
        return response({
          models: [
            {
              model_id: "deepseek:deepseek-v4-pro",
              id: "deepseek-v4-pro",
              name: "DeepSeek V4 Pro",
              provider: "deepseek",
              type: "text_generation",
              capabilities: ["text_generation"],
            },
          ],
        });
      }
      if (url.endsWith("/api/v1/tasks/7001")) {
        taskCalls += 1;
        return response({
          id: 7001,
          status: taskCalls === 1 ? "pending" : "completed",
          progress_detail:
            taskCalls === 1 ? "正在生成第2章正文" : "全部章节处理完成",
        });
      }
      if (url.endsWith("/novel/revisions")) {
        return response({
          items: [taskCalls >= 2 ? completedRevision : pendingRevision],
          canonical_business_id: null,
        });
      }
      throw new Error(`Unexpected request: ${url}`);
    };

    try {
      const utils = render(
        <StoryNovelWorkflowPanel
          story={story}
          onEpisodesApplied={async () => undefined}
          onTaskLockChange={(locked) => taskLocks.push(locked)}
        />,
        { container: dom.window.document.body },
      );

      await waitFor(() => assert.ok(utils.getByText("任务 #7001 · pending")));
      assertProgress(utils.container, "正文1/2", "facts/记忆0/2");
      assert.ok(utils.getByText("正文 body_ready"));
      assert.ok(utils.getByText("提取 blocked"));
      assert.equal(
        utils.getByLabelText("长度预设").hasAttribute("disabled"),
        true,
      );
      assert.equal(
        utils.getByLabelText("章前规划模型").hasAttribute("disabled"),
        true,
      );
      assert.equal(
        utils.getByLabelText("正文生成模型（可选）").hasAttribute("disabled"),
        true,
      );
      assert.equal(
        utils.getByLabelText("状态审计模型（可选）").hasAttribute("disabled"),
        true,
      );
      assert.equal(
        utils.getByLabelText("当前小说版本").hasAttribute("disabled"),
        true,
      );
      assert.equal(
        utils.getByLabelText("第1章正文").hasAttribute("disabled"),
        true,
      );
      assert.equal(taskLocks.at(-1), true);
      assert.ok(intervalRefresh);

      await act(async () => {
        await intervalRefresh?.();
      });

      await waitFor(() => assert.ok(utils.getByText("任务 #7001 · completed")));
      assertProgress(utils.container, "正文2/2", "facts/记忆1/2");
      assert.ok(utils.getByText("正文 state_pending"));
      assert.ok(utils.getByText("提取 ready"));
      assert.equal(
        utils.getByLabelText("长度预设").hasAttribute("disabled"),
        false,
      );
      await waitFor(() =>
        assert.equal(
          utils.getByLabelText("章前规划模型").hasAttribute("disabled"),
          false,
        ),
      );
      assert.equal(
        utils.getByLabelText("当前小说版本").hasAttribute("disabled"),
        false,
      );
      assert.equal(
        utils.getByLabelText("第1章正文").hasAttribute("disabled"),
        false,
      );
      assert.equal(taskLocks.at(-1), false);
    } finally {
      globalThis.fetch = originalFetch;
      dom.window.setInterval = originalSetInterval;
      dom.window.clearInterval = originalClearInterval;
    }
  });
});

function assertProgress(
  container: HTMLElement,
  bodyProgress: string,
  extractionProgress: string,
) {
  const text = container.textContent?.replace(/\s+/g, "") || "";
  assert.ok(text.includes(bodyProgress), text);
  assert.ok(text.includes(extractionProgress), text);
}

function response(data: unknown) {
  return new Response(JSON.stringify({ success: true, data }), {
    headers: { "content-type": "application/json" },
  });
}
