import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasVideoTaskStatus } from "../src/components/features/canvas/ProductionCanvasVideoTaskStatus";
import type { ProductionCanvasNode } from "../src/components/features/canvas/productionCanvasModel";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/canvas",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).SVGElement = dom.window.SVGElement;

const videoNode: ProductionCanvasNode = {
  id: "video-candidates",
  label: "Video Candidates",
  title: "视频候选",
  skill: "video.candidates",
  status: "running",
  width: 220,
  x: 0,
  y: 0,
  outputs: {
    canvas_task_id: 6289,
    dispatched_task_id: 701,
    task_status: "processing",
    task_progress_detail: "provider 已返回 1/2 个候选",
  },
};

describe("ProductionCanvasVideoTaskStatus", () => {
  afterEach(() => cleanup());

  it("shows the media task instead of the canvas planning task", () => {
    const utils = render(<ProductionCanvasVideoTaskStatus node={videoNode} />, {
      container: dom.window.document.body,
    });

    assert.ok(utils.getByText("视频任务 #701"));
    assert.ok(utils.getByText("生成中"));
    assert.ok(utils.getByText("进度：provider 已返回 1/2 个候选"));
    assert.equal(utils.queryByText("视频任务 #6289"), null);
  });

  it("retries a failed video task through node execution", () => {
    let retriedNode: ProductionCanvasNode | undefined;
    const failedNode: ProductionCanvasNode = {
      ...videoNode,
      status: "blocked",
      outputs: {
        ...videoNode.outputs,
        task_status: "failed",
        task_error_message: "provider quota exceeded",
      },
    };
    const utils = render(
      <ProductionCanvasVideoTaskStatus
        node={failedNode}
        onRetry={(node) => {
          retriedNode = node;
        }}
      />,
      { container: dom.window.document.body },
    );

    assert.ok(utils.getByText("错误：provider quota exceeded"));
    fireEvent.click(utils.getByRole("button", { name: "重试视频生成" }));
    assert.equal(retriedNode?.id, failedNode.id);
  });
});
