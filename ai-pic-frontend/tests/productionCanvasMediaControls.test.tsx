import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ProductionCanvasContent } from "../src/components/features/canvas/ProductionCanvasBoard";
import { ProductionCanvasMediaControls } from "../src/components/features/canvas/ProductionCanvasMediaControls";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).SVGElement = dom.window.SVGElement;
(globalThis as any).localStorage = dom.window.localStorage;
(globalThis as any).Event = dom.window.Event;
(globalThis as any).InputEvent = dom.window.InputEvent;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

describe("ProductionCanvasMediaControls", () => {
  afterEach(() => cleanup());

  it("sends selected media controls when executing image and video skills", async () => {
    const originalFetch = globalThis.fetch;
    const executeRequests: Record<string, any>[] = [];
    globalThis.fetch = async (input, init) => {
      const url = String(input);
      if (url.includes("/production-canvas/execute")) {
        const body = JSON.parse(String(init?.body));
        executeRequests.push(body);
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              task_id: body.skill === "image.candidates" ? 91 : 92,
              task_status: "pending",
              skill_result: {
                skill: body.skill,
                label:
                  body.skill === "image.candidates"
                    ? "Image Skill"
                    : "Video Skill",
                title: "已提交媒体任务",
                status: "running",
                detail: "后台已提交媒体任务。",
                outputs: {
                  script_id: body.script_id,
                  dispatched_task_id:
                    body.skill === "image.candidates" ? 91 : 92,
                  canvas_run_id: body.run_id,
                },
              },
            },
          }),
          { headers: { "content-type": "application/json" } },
        ) as Promise<Response>;
      }
      return new Response(
        JSON.stringify({
          success: true,
          data: {
            run_id: "canvas-run-media",
            task_id: 44,
            nodes: [
              {
                id: "skill-image",
                label: "Image Candidates",
                title: "图片候选执行入口",
                status: "blocked",
                x: 120,
                y: 320,
                width: 220,
                kind: "skill_result",
                skill: "image.candidates",
                detail: "复用现有分镜图片候选任务。",
                outputs: {
                  script_id: 321,
                  required_inputs: ["manual_media_controls"],
                },
              },
              {
                id: "skill-video",
                label: "Video Candidates",
                title: "视频候选执行入口",
                status: "blocked",
                x: 380,
                y: 320,
                width: 220,
                kind: "skill_result",
                skill: "video.candidates",
                detail: "复用现有分镜视频候选任务。",
                outputs: {
                  script_id: 321,
                  required_inputs: ["manual_media_controls"],
                },
              },
            ],
            selected_assets: { virtual_ips: [], environments: [] },
            skill_manifest: { version: "production_canvas.v1" },
          },
        }),
        { headers: { "content-type": "application/json" } },
      ) as Promise<Response>;
    };

    try {
      const utils = render(
        <ProductionCanvasContent storageKey={null} autosaveDelayMs={null} />,
        { container: dom.window.document.body },
      );
      fireEvent.input(utils.getByLabelText("生产目标"), {
        target: { value: "生成媒体候选" },
      });
      fireEvent.click(utils.getByRole("button", { name: "整体创建" }));
      await waitFor(() =>
        assert.ok(utils.getAllByText("图片候选执行入口").length),
      );

      fireEvent.click(
        utils.getByLabelText("Image Candidates 图片候选执行入口"),
      );
      fireEvent.input(utils.getByLabelText("媒体帧索引"), {
        target: { value: "1， 2 2" },
      });
      fireEvent.input(utils.getByLabelText("媒体模型"), {
        target: { value: "codex:gpt-image-2" },
      });
      fireEvent.input(utils.getByLabelText("图片画幅"), {
        target: { value: "16:9" },
      });
      fireEvent.click(utils.getByLabelText("要求参考图"));
      await waitFor(() => assert.ok(utils.getByText("frame_indexes: 1, 2")));
      fireEvent.click(utils.getByRole("button", { name: "运行节点" }));
      await waitFor(() =>
        assert.equal(executeRequests[0]?.skill, "image.candidates"),
      );
      assert.deepEqual(executeRequests[0]?.frame_indexes, [1, 2]);
      assert.equal(executeRequests[0]?.model, "codex:gpt-image-2");
      assert.equal(executeRequests[0]?.aspect_ratio, "16:9");
      assert.equal(executeRequests[0]?.require_reference_images, false);

      fireEvent.click(
        utils.getByLabelText("Video Candidates 视频候选执行入口"),
      );
      fireEvent.input(utils.getByLabelText("媒体帧索引"), {
        target: { value: "1、2 2" },
      });
      fireEvent.input(utils.getByLabelText("媒体模型"), {
        target: { value: "minimax:video-01" },
      });
      fireEvent.input(utils.getByLabelText("视频时长"), {
        target: { value: "6" },
      });
      fireEvent.input(utils.getByLabelText("视频 FPS"), {
        target: { value: "30" },
      });
      fireEvent.input(utils.getByLabelText("视频分辨率"), {
        target: { value: "1080p" },
      });
      fireEvent.input(utils.getByLabelText("视频画幅"), {
        target: { value: "16:9" },
      });
      fireEvent.click(utils.getByLabelText("固定镜头"));
      await waitFor(() => assert.ok(utils.getByText("duration: 6")));
      fireEvent.click(utils.getByRole("button", { name: "运行节点" }));
      await waitFor(() =>
        assert.equal(executeRequests[1]?.skill, "video.candidates"),
      );
      assert.deepEqual(executeRequests[1]?.frame_indexes, [1, 2]);
      assert.equal(executeRequests[1]?.model, "minimax:video-01");
      assert.equal(executeRequests[1]?.duration, 6);
      assert.equal(executeRequests[1]?.fps, 30);
      assert.equal(executeRequests[1]?.resolution, "1080p");
      assert.equal(executeRequests[1]?.ratio, "16:9");
      assert.equal(executeRequests[1]?.camera_fixed, true);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("drops non-positive video numeric parameters", () => {
    const patches: Record<string, unknown>[] = [];
    const utils = render(
      <ProductionCanvasMediaControls
        node={{
          id: "video-node",
          label: "Video Candidates",
          title: "视频候选执行入口",
          status: "blocked",
          x: 0,
          y: 0,
          width: 220,
          kind: "skill_result",
          skill: "video.candidates",
        }}
        onUpdateNodeOutputs={(_, patch) => patches.push(patch)}
      />,
      { container: dom.window.document.body },
    );

    fireEvent.input(utils.getByLabelText("视频时长"), {
      target: { value: "0" },
    });
    fireEvent.input(utils.getByLabelText("视频 FPS"), {
      target: { value: "-24" },
    });
    fireEvent.input(utils.getByLabelText("视频时长"), {
      target: { value: "6" },
    });

    assert.deepEqual(patches, [
      { duration: undefined },
      { fps: undefined },
      { duration: 6 },
    ]);
  });

  it("ignores malformed frame index tokens", () => {
    const patches: Record<string, unknown>[] = [];
    const utils = render(
      <ProductionCanvasMediaControls
        node={{
          id: "image-node",
          label: "Image Candidates",
          title: "图片候选执行入口",
          status: "blocked",
          x: 0,
          y: 0,
          width: 220,
          kind: "skill_result",
          skill: "image.candidates",
        }}
        onUpdateNodeOutputs={(_, patch) => patches.push(patch)}
      />,
      { container: dom.window.document.body },
    );

    fireEvent.input(utils.getByLabelText("媒体帧索引"), {
      target: { value: "1 3abc 2 2 -1" },
    });

    assert.deepEqual(patches, [{ frame_indexes: [1, 2] }]);
  });
});
