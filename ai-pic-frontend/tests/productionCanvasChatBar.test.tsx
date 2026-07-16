import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasChatBar } from "../src/components/features/canvas/ProductionCanvasChatBar";
import { emptyProductionCanvasContext } from "../src/components/features/canvas/productionCanvasContext";

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

describe("ProductionCanvasChatBar", () => {
  afterEach(() => cleanup());

  it("announces canvas creation errors", () => {
    const utils = render(
      <ProductionCanvasChatBar
        context={emptyProductionCanvasContext}
        error="整体创建失败"
        onCreate={() => {}}
        onContextChange={() => {}}
        onPromptChange={() => {}}
        prompt="生成短剧画布"
        running={false}
      />,
      { container: dom.window.document.body },
    );

    assert.equal(utils.getByRole("alert").textContent, "整体创建失败");
  });

  it("marks whole-canvas creation busy", () => {
    const utils = render(
      <ProductionCanvasChatBar
        context={emptyProductionCanvasContext}
        onCreate={() => {}}
        onContextChange={() => {}}
        onPromptChange={() => {}}
        prompt="生成短剧画布"
        running
      />,
      { container: dom.window.document.body },
    );

    const button = utils.getByRole("button", { name: "执行中" });
    assert.equal(button.getAttribute("aria-busy"), "true");
    assert.equal(button.hasAttribute("disabled"), true);
  });

  it("selects an episode without keeping a Story from another branch", () => {
    const changes: Array<[string, string]> = [];
    const utils = render(
      <ProductionCanvasChatBar
        assetOptions={{
          environments: [],
          episodes: [{ id: 12, name: "第 4 集 · 办公室危机" }],
          error: null,
          loading: false,
          scripts: [{ id: 34, name: "办公室危机 V2" }],
          virtualIPs: [],
        }}
        context={emptyProductionCanvasContext}
        onCreate={() => {}}
        onContextChange={(key, value) => changes.push([key, value])}
        onPromptChange={() => {}}
        prompt="生成短剧画布"
        running={false}
      />,
      { container: dom.window.document.body },
    );

    fireEvent.change(utils.getByLabelText("剧集"), {
      target: { value: "12" },
    });

    assert.deepEqual(changes, [
      ["story_id", ""],
      ["episode_id", "12"],
    ]);
  });

  it("selects canvas assets by name while emitting their numeric ids", () => {
    const changes: Array<[string, string]> = [];
    const utils = render(
      <ProductionCanvasChatBar
        assetOptions={{
          environments: [{ id: 22, name: "办公室" }],
          episodes: [],
          error: null,
          loading: false,
          scripts: [],
          virtualIPs: [{ id: 11, name: "林晚" }],
        }}
        context={emptyProductionCanvasContext}
        onCreate={() => {}}
        onContextChange={(key, value) => changes.push([key, value])}
        onPromptChange={() => {}}
        prompt="生成短剧画布"
        running={false}
      />,
      { container: dom.window.document.body },
    );

    fireEvent.change(utils.getByLabelText("IP 资产"), {
      target: { value: "11" },
    });
    fireEvent.change(utils.getByLabelText("环境资产"), {
      target: { value: "22" },
    });

    assert.deepEqual(changes, [
      ["virtual_ip_id", "11"],
      ["environment_id", "22"],
    ]);
  });

  it("shows lightweight single-video inputs without episode lineage fields", () => {
    const modeChanges: string[] = [];
    const utils = render(
      <ProductionCanvasChatBar
        assetOptions={{
          environments: [],
          episodes: [],
          error: null,
          loading: false,
          scripts: [],
          virtualIPs: [],
        }}
        creationMode="single_video"
        context={emptyProductionCanvasContext}
        onCreate={() => {}}
        onContextChange={() => {}}
        onCreationModeChange={(mode) => modeChanges.push(mode)}
        onPromptChange={() => {}}
        prompt="做一个三分钟产品视频"
        running={false}
      />,
      { container: dom.window.document.body },
    );

    assert.ok(utils.getByLabelText("视频标题"));
    assert.ok(utils.getByLabelText("视频时长"));
    assert.ok(utils.getByLabelText("视频画幅"));
    assert.ok(utils.getByLabelText("视频风格"));
    assert.equal(utils.queryByLabelText("剧集"), null);
    assert.equal(utils.queryByLabelText("剧本"), null);
    assert.equal(utils.queryByLabelText("任务 ID"), null);
    assert.ok(utils.getByRole("button", { name: "创建并生成" }));

    fireEvent.click(utils.getByRole("button", { name: "系列制作" }));
    assert.deepEqual(modeChanges, ["series"]);
  });
});
