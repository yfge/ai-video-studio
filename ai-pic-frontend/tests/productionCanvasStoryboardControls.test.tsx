import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasMediaControls } from "../src/components/features/canvas/ProductionCanvasMediaControls";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/canvas",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

describe("ProductionCanvas storyboard controls", () => {
  afterEach(() => cleanup());

  it("shows automatic panel sizing without keyframe controls", () => {
    const patches: Record<string, unknown>[] = [];
    const utils = render(
      <ProductionCanvasMediaControls
        node={{
          id: "storyboard-node",
          label: "Storyboard Candidates",
          title: "故事板候选",
          status: "blocked",
          x: 0,
          y: 0,
          width: 220,
          kind: "skill_result",
          skill: "storyboard.candidates",
        }}
        onUpdateNodeOutputs={(_, patch) => patches.push(patch)}
      />,
      { container: dom.window.document.body },
    );

    assert.ok(utils.getByText(/自动选择 2 \/ 4 \/ 6 \/ 9 格/));
    assert.equal(utils.queryByLabelText("媒体帧索引"), null);
    assert.equal(utils.queryByLabelText("图片画幅"), null);
    assert.equal(utils.queryByLabelText("视频时长"), null);
    fireEvent.input(utils.getByLabelText("媒体模型"), {
      target: { value: "codex:gpt-image-2" },
    });
    assert.deepEqual(patches, [{ model: "codex:gpt-image-2" }]);
  });
});
