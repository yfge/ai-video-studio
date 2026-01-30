import { describe, it, beforeEach, afterEach } from "node:test";
import assert from "node:assert";
import React from "react";
import { render, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { JSDOM } from "jsdom";
import { AlertModalProvider } from "../src/components/AlertModalProvider";
import { SceneStructurePanel } from "../src/components/SceneStructurePanel";
import apiClient from "../src/utils/api";

const dom = new JSDOM("<!doctype html><html><body></body></html>");
globalThis.window = dom.window as unknown as Window & typeof globalThis;
globalThis.document = dom.window.document;
globalThis.HTMLElement = dom.window.HTMLElement;
(globalThis as any).document = dom.window.document;
(globalThis as any).window = dom.window;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

const baseScene = {
  id: 1,
  scene_number: "1",
  slug_line: "INT. TEST - DAY",
  status: "draft",
};
const beat = { id: 10, order_index: 1, beat_summary: "beat" };
const shot = { id: 20, shot_number: "1A", shot_type: "WS" };

const withProvider = (ui: React.ReactNode) => (
  <AlertModalProvider>{ui}</AlertModalProvider>
);

describe("SceneStructurePanel permissions and callbacks", () => {
  let stubClient: any;

  beforeEach(() => {
    stubClient = {
      getNormalizedScenes: async () => ({ success: true, data: [baseScene] }),
      getNormalizedSceneBeats: async () => ({ success: true, data: [beat] }),
      getNormalizedSceneShots: async () => ({ success: true, data: [shot] }),
      createScene: async () => ({ success: true }),
      createSceneBeat: async () => ({ success: true }),
      createSceneShot: async () => ({ success: true }),
      updateSceneBeat: async () => ({ success: true }),
      updateSceneShot: async () => ({ success: true }),
      deleteSceneBeat: async () => ({ success: true }),
      deleteSceneShot: async () => ({ success: true }),
    };
    (apiClient as any).getNormalizedScenes = stubClient.getNormalizedScenes;
    (apiClient as any).getNormalizedSceneBeats =
      stubClient.getNormalizedSceneBeats;
    (apiClient as any).getNormalizedSceneShots =
      stubClient.getNormalizedSceneShots;
    (apiClient as any).createScene = stubClient.createScene;
  });

  afterEach(() => {
    cleanup();
  });

  it("blocks create when read-only and surfaces warning", async () => {
    let createCalls = 0;
    stubClient.createScene = async () => {
      createCalls += 1;
      return { success: true, data: {} };
    };

    const utils = render(
      withProvider(
        <SceneStructurePanel
          scriptId={123}
          canEdit={false}
          apiOverride={stubClient}
        />,
      ),
      { container: dom.window.document.body },
    );

    await utils.findByText("结构化场景 / 镜头");

    const badge = await utils.findByText(/只读 · 需管理员权限/i);
    assert.ok(badge);
    assert.strictEqual(createCalls, 0);
  });

  it("invokes onStructureLoaded with beats and shots", async () => {
    let loadedCount = 0;

    const utils = render(
      withProvider(
        <SceneStructurePanel
          scriptId={456}
          canEdit
          apiOverride={stubClient}
          onStructureLoaded={(scenes) => {
            loadedCount = scenes[0]?.beats?.length ?? 0;
          }}
        />,
      ),
      { container: dom.window.document.body },
    );

    await waitFor(() => {
      assert.ok(utils.getByText(/节拍 \(1\)/));
      assert.strictEqual(loadedCount, 1);
    });
  });
});
