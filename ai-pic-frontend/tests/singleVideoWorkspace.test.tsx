import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, render } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { EpisodeWorkspaceTimelineHeader } from "../src/components/features/episode/EpisodeWorkspaceTimelineHeader";
import { useEpisodeWorkspaceUrlState } from "../src/hooks/episode/useEpisodeWorkspaceUrlState";
import type { Episode } from "../src/utils/api/types";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

describe("single-video workspace", () => {
  afterEach(() => cleanup());

  it("reads the queued script task from the workspace URL", () => {
    function Harness() {
      const state = useEpisodeWorkspaceUrlState(
        new URLSearchParams("tab=script&taskId=77"),
      );
      return <span>{JSON.stringify(state)}</span>;
    }
    const utils = render(<Harness />, {
      container: dom.window.document.body,
    });
    const state = JSON.parse(
      utils.getByText(/initialScriptTaskId/).textContent!,
    );
    assert.equal(state.initialTab, "script");
    assert.equal(state.initialScriptTaskId, 77);
  });

  it("labels the internal Episode as a single video", () => {
    const episode = {
      id: 20,
      business_id: "episode-20",
      story_id: 10,
      episode_number: 1,
      title: "三分钟产品视频",
      status: "draft",
      created_at: "2026-07-16T00:00:00Z",
      updated_at: "2026-07-16T00:00:00Z",
    } as Episode;
    const utils = render(
      <EpisodeWorkspaceTimelineHeader
        episode={episode}
        scripts={[]}
        selectedScriptId={null}
        productionState={{
          steps: [
            { key: "script", label: "剧本", status: "pending" },
            { key: "timeline", label: "时间轴", status: "pending" },
            { key: "clip-video", label: "片段视频", status: "pending" },
            { key: "render-export", label: "渲染/导出", status: "pending" },
          ],
          primaryAction: { kind: "generate-script", label: "生成剧本" },
        }}
        singleVideoProject
        onTabChange={() => {}}
        onNavigateBack={() => {}}
        onSelectScript={() => {}}
        onPrimaryAction={() => {}}
      />,
      { container: dom.window.document.body },
    );

    assert.ok(utils.getByRole("heading", { name: "单条视频：三分钟产品视频" }));
    assert.equal(utils.queryByText(/第1集/), null);
  });
});
