import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import React from "react";
import { cleanup, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { useEpisodeMetadata } from "../src/hooks/useEpisodeMetadata";
import type { Episode, Script } from "../src/utils/api/types";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).localStorage = dom.window.localStorage;

const originalFetch = globalThis.fetch;

const episode = {
  id: 194,
  business_id: "episode-business-id",
  story_id: 62,
  episode_number: 1,
  title: "单条视频",
  status: "draft",
  created_at: "2026-07-18T00:00:00Z",
  updated_at: "2026-07-18T00:00:00Z",
} satisfies Episode;

const script = {
  id: 146,
  business_id: "script-business-id",
  episode_id: 194,
  title: "单条视频剧本",
  format_type: "screenplay",
  language: "zh-CN",
  status: "draft",
  version: "1.0",
  created_at: "2026-07-18T00:00:00Z",
  updated_at: "2026-07-18T00:00:00Z",
} satisfies Script;

function MetadataHarness({ renderStates }: { renderStates: boolean[] }) {
  const metadata = useEpisodeMetadata(episode, script);
  renderStates.push(metadata.timelineSpecLoading);
  return <div>{metadata.timelineSpecLoading ? "loading" : "ready"}</div>;
}

describe("episode Timeline metadata loading", () => {
  afterEach(() => {
    cleanup();
    globalThis.fetch = originalFetch;
  });

  it("is loading on the first render for a new episode and script pair", async () => {
    globalThis.fetch = (async (url: RequestInfo | URL) => {
      assert.equal(String(url), "/api/v1/episodes/194/timelines");
      return new Response(JSON.stringify({ items: [] }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }) as typeof fetch;
    const renderStates: boolean[] = [];

    const utils = render(<MetadataHarness renderStates={renderStates} />, {
      container: dom.window.document.body,
    });

    assert.equal(renderStates[0], true);
    await waitFor(() => assert.ok(utils.getByText("ready")));
  });
});
