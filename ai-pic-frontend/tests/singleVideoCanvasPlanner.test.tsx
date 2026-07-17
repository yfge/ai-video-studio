import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { useProductionCanvasSkillPlanner } from "../src/components/features/canvas/useProductionCanvasSkillPlanner";
import { runSingleVideoCanvasCreation } from "../src/components/features/canvas/useProductionCanvasSingleVideoPlanner";
import type { ProductionCanvasNode } from "../src/components/features/canvas/productionCanvasModel";
import { emptyProductionCanvasContext } from "../src/components/features/canvas/productionCanvasContext";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/canvas",
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

const originalFetch = globalThis.fetch;

describe("single-video canvas planner", () => {
  afterEach(() => {
    cleanup();
    globalThis.fetch = originalFetch;
    dom.window.document.body.replaceChildren();
  });

  it("plans structured context and executes only script.generate", async () => {
    const requests: Array<{ url: string; body: Record<string, unknown> }> = [];
    globalThis.fetch = (async (input, init) => {
      const url = String(input);
      const body = JSON.parse(String(init?.body || "{}")) as Record<
        string,
        unknown
      >;
      requests.push({ url, body });
      if (url.includes("/api/v1/production-canvas/plan")) {
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              prompt: body.prompt,
              run_id: "run-single-video",
              task_id: 901,
              resolved_context: { story_id: 101, episode_id: 202 },
              skill_manifest: {
                version: "production_canvas.v1",
                skills: [],
              },
              selected_assets: { virtual_ips: [], environments: [] },
              production_context: {
                brief: { ready_for_execution: true },
              },
              nodes: [
                {
                  id: "script-generate",
                  label: "Script Skill",
                  title: "生成单条视频剧本",
                  status: "ready",
                  x: 100,
                  y: 100,
                  width: 220,
                  kind: "skill_result",
                  skill: "script.generate",
                  detail: "复用现有剧本 worker",
                  outputs: {
                    story_id: 101,
                    episode_id: 202,
                    planning_mode: "single_video",
                  },
                  reuse_targets: [],
                },
                {
                  id: "image-candidates",
                  label: "Image Skill",
                  title: "图片候选",
                  status: "blocked",
                  x: 400,
                  y: 100,
                  width: 220,
                  kind: "skill_result",
                  skill: "image.candidates",
                  detail: "等待显式执行",
                  outputs: { story_id: 101, episode_id: 202 },
                  reuse_targets: [],
                },
              ],
            },
          }),
          { headers: { "content-type": "application/json" } },
        );
      }
      if (url.includes("/api/v1/production-canvas/execute")) {
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              task_id: 303,
              task_status: "pending",
              node_id: "script-generate",
              skill_result: {
                skill: "script.generate",
                label: "Script Skill",
                status: "running",
                title: "已提交剧本生成",
                detail: "等待任务完成",
                outputs: {
                  story_id: 101,
                  episode_id: 202,
                  dispatched_task_id: 303,
                  task_status: "pending",
                  canvas_run_id: "run-single-video",
                },
                reuse_targets: [],
              },
            },
          }),
          { headers: { "content-type": "application/json" } },
        );
      }
      throw new Error(`Unexpected request ${url}`);
    }) as typeof fetch;

    const nodeUpdates: ProductionCanvasNode[][] = [];
    function Harness() {
      const planner = useProductionCanvasSkillPlanner({
        nodes: [],
        onNodesCreated: (nodes) => nodeUpdates.push(nodes),
        onRunCreated: () => {},
        taskPollIntervalMs: 60_000,
      });
      return (
        <>
          <button
            type="button"
            onClick={() => planner.setCreationMode("single_video")}
          >
            single mode
          </button>
          <input
            aria-label="canvas prompt"
            value={planner.prompt}
            onChange={(event) => planner.setPrompt(event.target.value)}
            onInput={(event) => planner.setPrompt(event.currentTarget.value)}
          />
          <button
            type="button"
            onClick={() =>
              planner.setPlanningSettings({
                durationSeconds: "300",
                aspectRatio: "16:9",
                visualStyle: "明亮科技感",
              })
            }
          >
            configure video
          </button>
          <button type="button" onClick={() => void planner.createFromPrompt()}>
            create video
          </button>
          <span data-testid="planner-error">{planner.error || ""}</span>
          <span data-testid="planner-mode">{planner.creationMode}</span>
          <span data-testid="planner-prompt">{planner.prompt}</span>
          <span data-testid="planner-running">{String(planner.running)}</span>
        </>
      );
    }

    const utils = render(<Harness />, {
      container: dom.window.document.body,
    });
    fireEvent.click(utils.getByRole("button", { name: "single mode" }));
    fireEvent.input(utils.getByLabelText("canvas prompt"), {
      target: { value: "介绍桌面机器人，突出三项卖点" },
    });
    fireEvent.click(utils.getByRole("button", { name: "configure video" }));
    fireEvent.click(utils.getByRole("button", { name: "create video" }));

    await waitFor(
      () =>
        assert.equal(
          requests.filter((request) =>
            request.url.includes("/production-canvas/execute"),
          ).length,
          1,
          JSON.stringify({
            requests,
            error: utils.getByTestId("planner-error").textContent,
            mode: utils.getByTestId("planner-mode").textContent,
            prompt: utils.getByTestId("planner-prompt").textContent,
            running: utils.getByTestId("planner-running").textContent,
          }),
        ),
      { timeout: 3000 },
    );
    assert.deepEqual(
      requests.map((request) =>
        request.url.includes("/production-canvas/plan") ? "plan" : "execute",
      ),
      ["plan", "execute"],
    );
    assert.deepEqual(requests[0].body, {
      prompt: "介绍桌面机器人，突出三项卖点",
      planning_mode: "single_video",
      brief_overrides: {
        duration_seconds: 300,
        aspect_ratio: "16:9",
        visual_style: "明亮科技感",
      },
      clarification_answers: {},
    });
    assert.equal(requests[1].body.skill, "script.generate");
    assert.equal(requests[1].body.planning_mode, "single_video");
    assert.equal(
      requests.some((request) => request.body.skill === "image.candidates"),
      false,
    );
    assert.ok(nodeUpdates[0].some((node) => node.skill === "image.candidates"));
  });

  it("keeps the plan blocked while a required clarification is unanswered", async () => {
    globalThis.fetch = (async () =>
      new Response(
        JSON.stringify({
          success: true,
          data: {
            prompt: "做一条品牌短片",
            run_id: "run-needs-answer",
            resolved_context: {},
            production_context: {
              brief: {
                ready_for_execution: false,
                clarifications: [
                  {
                    id: "virtual_ip",
                    question: "请选择要复用的 IP",
                    required: true,
                    answer: null,
                  },
                ],
              },
            },
            nodes: [
              {
                id: "script-generate",
                label: "Script Skill",
                title: "生成剧本",
                status: "ready",
                x: 100,
                y: 100,
                width: 220,
                kind: "skill_result",
                skill: "script.generate",
                detail: "等待上下文",
                outputs: {},
                reuse_targets: [],
              },
            ],
          },
        }),
        { headers: { "content-type": "application/json" } },
      )) as typeof fetch;

    let executionCount = 0;
    let receivedContext: unknown = null;
    await runSingleVideoCanvasCreation({
      captureIdentity: () => ({ runId: "", epoch: 1 }),
      contextRef: { current: { ...emptyProductionCanvasContext } },
      draft: { title: "" },
      briefOverrides: {},
      clarificationAnswers: {},
      executeScript: async () => {
        executionCount += 1;
        return [];
      },
      isCurrent: () => true,
      onIdentityChange: () => undefined,
      onNodesCreated: () => undefined,
      onProductionContext: (context) => {
        receivedContext = context;
      },
      prompt: "做一条品牌短片",
      publish: () => undefined,
      replaceContext: () => undefined,
      setExecutingNodeId: () => undefined,
    });

    assert.equal(executionCount, 0);
    assert.equal(
      (receivedContext as { brief?: { ready_for_execution?: boolean } })?.brief
        ?.ready_for_execution,
      false,
    );
  });
});
