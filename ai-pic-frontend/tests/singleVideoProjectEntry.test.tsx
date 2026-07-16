import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { SingleVideoProjectModal } from "../src/components/features/stories/SingleVideoProjectModal";
import { StoryListSection } from "../src/components/features/stories/StoryListSection";
import type { SingleVideoProjectResponse, Story } from "../src/utils/api/types";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/stories",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).localStorage = dom.window.localStorage;
(globalThis as any).Event = dom.window.Event;
(globalThis as any).InputEvent = dom.window.InputEvent;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

const originalFetch = globalThis.fetch;

describe("single-video project entry", () => {
  afterEach(() => {
    cleanup();
    globalThis.fetch = originalFetch;
    dom.window.document.body.replaceChildren();
  });

  it("creates a project from only a video description and chosen format", async () => {
    let requestBody: Record<string, unknown> | null = null;
    const created: SingleVideoProjectResponse[] = [];
    globalThis.fetch = (async (_input, init) => {
      requestBody = JSON.parse(String(init?.body || "{}"));
      return new Response(
        JSON.stringify({
          story_id: 10,
          story_business_id: "story-10",
          episode_id: 20,
          episode_business_id: "episode-20",
          task_id: 30,
          task_status: "pending",
          context: { story_id: 10, episode_id: 20, task_id: 30 },
        }),
        { status: 201, headers: { "content-type": "application/json" } },
      );
    }) as typeof fetch;

    const utils = render(
      <SingleVideoProjectModal
        open
        onClose={() => {}}
        onCreated={(project) => created.push(project)}
      />,
      { container: dom.window.document.body },
    );

    fireEvent.input(utils.getByLabelText("视频描述"), {
      target: { value: "介绍桌面机器人，包含三项卖点和行动号召" },
    });
    fireEvent.change(utils.getByLabelText("视频时长"), {
      target: { value: "5" },
    });
    fireEvent.change(utils.getByLabelText("视频画幅"), {
      target: { value: "16:9" },
    });
    fireEvent.input(utils.getByLabelText("视频风格（可选）"), {
      target: { value: "明亮科技感" },
    });
    fireEvent.submit(
      utils.container.querySelector("#single-video-project-form")!,
    );

    await waitFor(() =>
      assert.equal(
        created.length,
        1,
        JSON.stringify({
          requestBody,
          prompt: (utils.getByLabelText("视频描述") as HTMLTextAreaElement)
            .value,
          error: utils.queryByRole("alert")?.textContent || "",
        }),
      ),
    );
    assert.deepEqual(requestBody, {
      title: "介绍桌面机器人，包含三项卖点和行动号召",
      prompt: "介绍桌面机器人，包含三项卖点和行动号召",
      duration_minutes: 5,
      aspect_ratio: "16:9",
      style: "明亮科技感",
      start_generation: true,
    });
    assert.equal(created[0].episode_id, 20);
  });

  it("presents internal single-video records as direct video projects", () => {
    const story = {
      id: 10,
      business_id: "story-10",
      title: "三分钟产品视频",
      genre: "single_video",
      duration_minutes: 3,
      default_aspect_ratio: "9:16",
      synopsis: "介绍桌面机器人",
      status: "draft",
      is_public: false,
      story_characters: [],
      extra_metadata: {
        creation_mode: "single_video",
        episode_id: 20,
        script_task_id: 30,
      },
      created_at: "2026-07-16T00:00:00Z",
      updated_at: "2026-07-16T00:00:00Z",
    } as Story;
    const utils = render(
      <StoryListSection
        stories={[story]}
        loading={false}
        selectedGenre=""
        onSelectedGenreChange={() => {}}
        selectedStatus=""
        onSelectedStatusChange={() => {}}
        onOpenSingleVideoForm={() => {}}
        onOpenGenerateForm={() => {}}
        onDelete={() => {}}
      />,
      { container: dom.window.document.body },
    );

    const link = utils.getByRole("link", { name: "打开视频" });
    assert.equal(
      link.getAttribute("href"),
      "/episodes/20/workspace?tab=script&taskId=30",
    );
    assert.equal(utils.queryByRole("link", { name: "生成剧集" }), null);
    assert.ok(utils.getByText("无需预先配置 IP"));
  });
});
