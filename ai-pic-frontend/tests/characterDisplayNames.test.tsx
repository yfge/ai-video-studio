import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, render } from "@testing-library/react";
import { JSDOM } from "jsdom";
import React from "react";

import { CharacterRow } from "../src/components/features/episode/CharacterRow";
import { StoryboardCharacterIpSelector } from "../src/components/features/episode/TimelineClipStoryboardCharacterIpSelector";
import { StoryListSection } from "../src/components/features/stories/StoryListSection";
import type { EpisodeCharacter, Story } from "../src/utils/api/types";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).HTMLInputElement = dom.window.HTMLInputElement;

describe("character display names", () => {
  afterEach(() => cleanup());

  it("renders story IP chips from the backend display name", () => {
    const utils = render(
      <StoryListSection
        stories={[storyWithIpDisplayName()]}
        loading={false}
        selectedGenre=""
        onSelectedGenreChange={() => undefined}
        selectedStatus=""
        onSelectedStatusChange={() => undefined}
        onOpenGenerateForm={() => undefined}
        onDelete={() => undefined}
      />,
      { container: dom.window.document.body },
    );

    assert.ok(utils.getByText("IP: 林晚模板"));
    assert.equal(utils.queryByText(/未命名/), null);
  });

  it("renders episode character rows from the backend display name", () => {
    const utils = render(
      <CharacterRow
        character={episodeCharacterWithIpDisplayName()}
        onEdit={() => undefined}
        onDelete={() => undefined}
      />,
      { container: dom.window.document.body },
    );

    assert.ok(utils.getByText("快递员模板"));
    assert.equal(utils.queryByText(/未命名/), null);
  });

  it("renders clip storyboard IP selector labels from the backend display name", () => {
    const utils = render(
      <StoryboardCharacterIpSelector
        characters={[episodeCharacterWithIpDisplayName()]}
        loading={false}
        error={null}
        selectedVirtualIpIds={[]}
        onToggle={() => undefined}
      />,
      { container: dom.window.document.body },
    );

    assert.ok(utils.getByLabelText("绑定角色 IP 快递员模板"));
    assert.equal(utils.queryByText("未命名角色"), null);
  });
});

function storyWithIpDisplayName(): Story {
  return {
    id: 1,
    business_id: "story_1",
    title: "测试故事",
    genre: "Drama",
    status: "draft",
    is_public: false,
    created_at: "2026-06-09T00:00:00Z",
    updated_at: "2026-06-09T00:00:00Z",
    story_characters: [
      {
        id: 11,
        business_id: "story_char_11",
        story_id: 1,
        importance: 5,
        virtual_ip_id: 31,
        virtual_ip_business_id: "vip_31",
        character_name: null,
        virtual_ip_name: "林晚模板",
        display_name: "林晚模板",
        created_at: "2026-06-09T00:00:00Z",
        updated_at: "2026-06-09T00:00:00Z",
      },
    ],
  } as Story;
}

function episodeCharacterWithIpDisplayName(): EpisodeCharacter {
  return {
    id: 1032,
    business_id: "ep_char_32",
    episode_id: 1,
    episode_business_id: "episode_1",
    virtual_ip_id: 32,
    virtual_ip_business_id: "vip_32",
    character_name: null,
    virtual_ip_name: "快递员模板",
    display_name: "快递员模板",
    role_type: "temporary",
    importance: 3,
    created_at: "2026-06-09T00:00:00Z",
    updated_at: "2026-06-09T00:00:00Z",
  } as EpisodeCharacter;
}
