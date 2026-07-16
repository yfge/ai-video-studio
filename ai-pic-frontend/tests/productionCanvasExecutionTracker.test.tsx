import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { act, cleanup, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { useProductionCanvasExecutionTracker } from "../src/components/features/canvas/useProductionCanvasExecutionTracker";
import type { ProductionCanvasNode } from "../src/components/features/canvas/productionCanvasModel";
import type { ProductionCanvasResolvedContext } from "../src/utils/api/types";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/canvas",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).localStorage = dom.window.localStorage;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

const sourceNode: ProductionCanvasNode = {
  id: "skill-environment-image",
  label: "Environment Image",
  title: "Queue environment image",
  status: "ready",
  x: 0,
  y: 0,
  width: 220,
};
const runningSkillNode: ProductionCanvasNode = {
  ...sourceNode,
  status: "running",
  outputs: { dispatched_task_id: 101, task_status: "pending" },
};
const taskNode: ProductionCanvasNode = {
  id: "skill-environment-image-task-101",
  kind: "note",
  label: "Task #101",
  title: "Environment task",
  status: "running",
  x: 0,
  y: 120,
  width: 220,
  outputs: { source_node_id: sourceNode.id, task_id: 101 },
};

const renderSkillNode: ProductionCanvasNode = {
  ...sourceNode,
  id: "skill-timeline-render",
  skill: "timeline.render",
  status: "running",
  outputs: {
    timeline_id: 71,
    render_job_id: 122,
    render_status: "queued",
  },
};
const renderNode: ProductionCanvasNode = {
  ...taskNode,
  id: "skill-timeline-render-render-122",
  label: "Render #122",
  outputs: {
    source_node_id: renderSkillNode.id,
    timeline_id: 71,
    render_job_id: 122,
    render_status: "queued",
  },
};

describe("useProductionCanvasExecutionTracker", () => {
  afterEach(() => cleanup());

  it("polls a dispatched task and updates both canvas nodes with its artifact", async () => {
    const originalFetch = globalThis.fetch;
    const updates: ProductionCanvasNode[][] = [];
    const resolvedContexts: ProductionCanvasResolvedContext[] = [];
    globalThis.fetch = async (input) => {
      assert.equal(String(input), "/api/v1/tasks/101");
      return new Response(
        JSON.stringify({
          id: 101,
          business_id: "task-101",
          title: "环境图已完成",
          status: "completed",
          result_file_path: "environment_images:13:1",
          result_context: {
            story_id: 10,
            episode_id: 20,
            script_id: 30,
            timeline_id: 40,
            timeline_version: 5,
            clip_id: "clip-6",
          },
          created_at: "2026-07-10T10:00:00Z",
          user_id: 1,
        }),
        { headers: { "content-type": "application/json" } },
      );
    };

    function Harness() {
      const publish = useProductionCanvasExecutionTracker({
        onDomainContextResolved: (context) => resolvedContexts.push(context),
        onNodesCreated: (nodes) => updates.push(nodes),
        pollIntervalMs: 5,
        maxPollMs: 500,
      });
      return (
        <button
          type="button"
          onClick={() => publish(sourceNode, [runningSkillNode, taskNode])}
        >
          publish
        </button>
      );
    }

    try {
      const utils = render(<Harness />, {
        container: dom.window.document.body,
      });
      utils.getByRole("button", { name: "publish" }).click();

      await waitFor(() => assert.equal(updates.length, 2));
      assert.equal(updates[1][0].status, "review");
      assert.equal(updates[1][1].outputs?.task_status, "completed");
      assert.equal(
        updates[1][0].outputs?.result_file_path,
        "environment_images:13:1",
      );
      assert.equal(updates[1][0].outputs?.timeline_id, 40);
      assert.deepEqual(resolvedContexts, [
        {
          story_id: 10,
          episode_id: 20,
          script_id: 30,
          timeline_id: 40,
          timeline_version: 5,
          clip_id: "clip-6",
          task_id: 101,
        },
      ]);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("polls a RenderJob until the final video link is ready", async () => {
    const originalFetch = globalThis.fetch;
    const updates: ProductionCanvasNode[][] = [];
    let requestCount = 0;
    globalThis.fetch = async (input) => {
      assert.equal(String(input), "/api/v1/timelines/71/render-jobs");
      requestCount += 1;
      const succeeded = requestCount > 1;
      return new Response(
        JSON.stringify({
          items: [
            {
              id: 122,
              business_id: "render-122",
              timeline_id: 71,
              timeline_version: 6,
              render_type: "final",
              preset_hash: "preset",
              preset: { fps: 24 },
              status: succeeded ? "succeeded" : "running",
              progress: succeeded ? 100 : 50,
              output_asset_id: succeeded ? 375 : null,
              output_asset: succeeded
                ? {
                    id: 375,
                    business_id: "asset-375",
                    asset_type: "video",
                    origin: "timeline_render",
                    file_url: "/media/final.mp4",
                    created_at: "2026-07-10T10:00:00Z",
                    updated_at: "2026-07-10T10:00:00Z",
                  }
                : null,
              created_at: "2026-07-10T10:00:00Z",
              updated_at: "2026-07-10T10:00:01Z",
            },
          ],
        }),
        { headers: { "content-type": "application/json" } },
      );
    };

    function Harness() {
      const publish = useProductionCanvasExecutionTracker({
        onNodesCreated: (nodes) => updates.push(nodes),
        pollIntervalMs: 5,
        maxPollMs: 500,
      });
      return (
        <button
          type="button"
          onClick={() =>
            publish(renderSkillNode, [renderSkillNode, renderNode])
          }
        >
          publish render
        </button>
      );
    }

    try {
      const utils = render(<Harness />, {
        container: dom.window.document.body,
      });
      utils.getByRole("button", { name: "publish render" }).click();

      await waitFor(() => assert.equal(updates.length, 3));
      assert.equal(updates[1][0].outputs?.render_progress, 50);
      assert.equal(updates[2][0].status, "ready");
      assert.equal(updates[2][1].outputs?.render_status, "succeeded");
      assert.equal(updates[2][0].actionHref, "/media/final.mp4");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("ignores an old run task response after the same node starts in a new run", async () => {
    const originalFetch = globalThis.fetch;
    const updates: ProductionCanvasNode[][] = [];
    const resolvedContexts: ProductionCanvasResolvedContext[] = [];
    let resolveRunATask: ((response: Response) => void) | undefined;
    let resolveRunBTask: ((response: Response) => void) | undefined;
    const completedTask = (taskId: number, storyId: number) =>
      new Response(
        JSON.stringify({
          id: taskId,
          business_id: `task-${taskId}`,
          title: `任务 ${taskId} 已完成`,
          status: "completed",
          result_context: { story_id: storyId },
          created_at: "2026-07-10T10:00:00Z",
          user_id: 1,
        }),
        { headers: { "content-type": "application/json" } },
      );
    globalThis.fetch = async (input) => {
      const url = String(input);
      if (url.includes("/production-canvas/runs/run-")) {
        const runId = url.endsWith("run-a") ? "run-a" : "run-b";
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              run_id: runId,
              task_id: 1,
              nodes: [],
              selected_assets: { virtual_ips: [], environments: [] },
              skill_manifest: { version: "production_canvas.v1" },
            },
          }),
          { headers: { "content-type": "application/json" } },
        );
      }
      if (url === "/api/v1/tasks/101") {
        return new Promise<Response>((resolve) => {
          resolveRunATask = resolve;
        });
      }
      if (url === "/api/v1/tasks/202") {
        return new Promise<Response>((resolve) => {
          resolveRunBTask = resolve;
        });
      }
      throw new Error(`Unexpected request ${url}`);
    };

    const executionNodes = (runId: string, taskId: number) => [
      {
        ...runningSkillNode,
        outputs: {
          canvas_run_id: runId,
          dispatched_task_id: taskId,
          task_status: "pending",
        },
      },
      {
        ...taskNode,
        id: `${sourceNode.id}-task-${taskId}`,
        label: `Task #${taskId}`,
        outputs: {
          canvas_run_id: runId,
          source_node_id: sourceNode.id,
          task_id: taskId,
        },
      },
    ];

    function Harness({ runId }: { runId: string }) {
      const publish = useProductionCanvasExecutionTracker({
        onDomainContextResolved: (context) => resolvedContexts.push(context),
        onNodesCreated: (nodes) => updates.push(nodes),
        pollIntervalMs: 5,
        maxPollMs: 500,
        runId,
      });
      return (
        <button
          type="button"
          onClick={() => {
            const taskId = runId === "run-a" ? 101 : 202;
            publish(sourceNode, executionNodes(runId, taskId), runId);
          }}
        >
          publish {runId}
        </button>
      );
    }

    try {
      const utils = render(<Harness runId="run-a" />, {
        container: dom.window.document.body,
      });
      utils.getByRole("button", { name: "publish run-a" }).click();
      await waitFor(() => assert.ok(resolveRunATask));

      utils.rerender(<Harness runId="run-b" />);
      utils.getByRole("button", { name: "publish run-b" }).click();
      await waitFor(() => assert.ok(resolveRunBTask));
      await act(async () => {
        resolveRunATask?.(completedTask(101, 101));
        await new Promise((resolve) => setTimeout(resolve, 0));
      });
      assert.equal(updates.length, 2);
      assert.deepEqual(resolvedContexts, []);

      await act(async () => {
        resolveRunBTask?.(completedTask(202, 202));
      });
      await waitFor(() => assert.equal(updates.length, 3));
      assert.equal(updates[2][0].outputs?.task_id, 202);
      assert.equal(updates[2][0].outputs?.story_id, 202);
      assert.deepEqual(resolvedContexts, [{ story_id: 202, task_id: 202 }]);
    } finally {
      resolveRunATask?.(completedTask(101, 101));
      resolveRunBTask?.(completedTask(202, 202));
      globalThis.fetch = originalFetch;
    }
  });

  it("ignores a late task response after resetting a null-Run canvas", async () => {
    const originalFetch = globalThis.fetch;
    const updates: ProductionCanvasNode[][] = [];
    const resolvedContexts: ProductionCanvasResolvedContext[] = [];
    let resolveTask: ((response: Response) => void) | undefined;
    globalThis.fetch = async (input) => {
      assert.equal(String(input), "/api/v1/tasks/101");
      return new Promise<Response>((resolve) => {
        resolveTask = resolve;
      });
    };

    function Harness({ epoch }: { epoch: number }) {
      const publish = useProductionCanvasExecutionTracker({
        operationEpoch: epoch,
        onDomainContextResolved: (context) => resolvedContexts.push(context),
        onNodesCreated: (nodes) => updates.push(nodes),
        pollIntervalMs: 5,
        maxPollMs: 500,
        runId: null,
      });
      return (
        <button
          type="button"
          onClick={() => publish(sourceNode, [runningSkillNode, taskNode])}
        >
          publish fresh
        </button>
      );
    }

    try {
      const utils = render(<Harness epoch={0} />, {
        container: dom.window.document.body,
      });
      utils.getByRole("button", { name: "publish fresh" }).click();
      await waitFor(() => assert.ok(resolveTask));
      utils.rerender(<Harness epoch={1} />);
      await act(
        async () =>
          resolveTask?.(
            new Response(
              JSON.stringify({
                id: 101,
                business_id: "task-101",
                title: "late task",
                status: "completed",
                result_context: { story_id: 301 },
                created_at: "2026-07-15T10:00:00Z",
                user_id: 1,
              }),
              { headers: { "content-type": "application/json" } },
            ),
          ),
      );
      assert.equal(updates.length, 1);
      assert.deepEqual(resolvedContexts, []);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("marks a same-Run task stale when its context fingerprint changed", async () => {
    const originalFetch = globalThis.fetch;
    const updates: ProductionCanvasNode[][] = [];
    const contexts: ProductionCanvasResolvedContext[] = [];
    let fingerprint = "story:10";
    let resolveTask: ((response: Response) => void) | undefined;
    globalThis.fetch = async (input) => {
      if (String(input).includes("/production-canvas/runs/run-a")) {
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              run_id: "run-a",
              task_id: 1,
              nodes: [],
              selected_assets: { virtual_ips: [], environments: [] },
              skill_manifest: { version: "production_canvas.v1" },
            },
          }),
          { headers: { "content-type": "application/json" } },
        );
      }
      return new Promise<Response>((resolve) => {
        resolveTask = resolve;
      });
    };

    function Harness() {
      const publish = useProductionCanvasExecutionTracker({
        captureContextFingerprint: () => fingerprint,
        onDomainContextResolved: (context) => contexts.push(context),
        onNodesCreated: (nodes) => updates.push(nodes),
        pollIntervalMs: 5,
        maxPollMs: 500,
        runId: "run-a",
      });
      return (
        <button
          type="button"
          onClick={() =>
            publish(sourceNode, [runningSkillNode, taskNode], "run-a")
          }
        >
          publish fingerprint
        </button>
      );
    }

    try {
      const utils = render(<Harness />, {
        container: dom.window.document.body,
      });
      utils.getByRole("button", { name: "publish fingerprint" }).click();
      await waitFor(() => assert.ok(resolveTask));
      fingerprint = "story:11";
      await act(
        async () =>
          resolveTask?.(
            new Response(
              JSON.stringify({
                id: 101,
                business_id: "task-101",
                title: "old branch task",
                status: "completed",
                result_context: { story_id: 10 },
                created_at: "2026-07-15T10:00:00Z",
                user_id: 1,
              }),
              { headers: { "content-type": "application/json" } },
            ),
          ),
      );

      await waitFor(() => assert.equal(updates.length, 2));
      assert.equal(updates[1][0].status, "stale");
      assert.equal(updates[1][1].outputs?.task_status, "stale");
      assert.deepEqual(contexts, []);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("settles a cancelled Task as blocked instead of leaving it running", async () => {
    const originalFetch = globalThis.fetch;
    const updates: ProductionCanvasNode[][] = [];
    globalThis.fetch = async () =>
      new Response(
        JSON.stringify({
          id: 101,
          business_id: "task-101",
          title: "cancelled task",
          status: "cancelled",
          created_at: "2026-07-15T10:00:00Z",
          user_id: 1,
        }),
        { headers: { "content-type": "application/json" } },
      );

    function Harness() {
      const publish = useProductionCanvasExecutionTracker({
        onNodesCreated: (nodes) => updates.push(nodes),
        pollIntervalMs: 5,
        maxPollMs: 500,
      });
      return (
        <button
          type="button"
          onClick={() => publish(sourceNode, [runningSkillNode, taskNode])}
        >
          publish cancelled
        </button>
      );
    }

    try {
      const utils = render(<Harness />, {
        container: dom.window.document.body,
      });
      utils.getByRole("button", { name: "publish cancelled" }).click();

      await waitFor(() => assert.equal(updates.length, 2));
      assert.equal(updates[1][0].status, "blocked");
      assert.equal(updates[1][1].outputs?.task_status, "cancelled");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("settles an overdue Task as timeout instead of leaving it running", async () => {
    const originalFetch = globalThis.fetch;
    const updates: ProductionCanvasNode[][] = [];
    globalThis.fetch = async () =>
      new Response(
        JSON.stringify({
          id: 101,
          business_id: "task-101",
          title: "pending task",
          status: "pending",
          created_at: "2026-07-15T10:00:00Z",
          user_id: 1,
        }),
        { headers: { "content-type": "application/json" } },
      );

    function Harness() {
      const publish = useProductionCanvasExecutionTracker({
        onNodesCreated: (nodes) => updates.push(nodes),
        pollIntervalMs: 5,
        maxPollMs: 10,
      });
      return (
        <button
          type="button"
          onClick={() => publish(sourceNode, [runningSkillNode, taskNode])}
        >
          publish task timeout
        </button>
      );
    }

    try {
      const utils = render(<Harness />, {
        container: dom.window.document.body,
      });
      utils.getByRole("button", { name: "publish task timeout" }).click();

      await waitFor(() => assert.equal(updates.length, 2));
      assert.equal(updates[1][0].status, "blocked");
      assert.equal(updates[1][1].outputs?.task_status, "timeout");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("settles an overdue Render as timeout instead of leaving it running", async () => {
    const originalFetch = globalThis.fetch;
    const updates: ProductionCanvasNode[][] = [];
    globalThis.fetch = async () =>
      new Response(JSON.stringify({ items: [] }), {
        headers: { "content-type": "application/json" },
      });

    function Harness() {
      const publish = useProductionCanvasExecutionTracker({
        onNodesCreated: (nodes) => updates.push(nodes),
        pollIntervalMs: 5,
        maxPollMs: 10,
      });
      return (
        <button
          type="button"
          onClick={() =>
            publish(renderSkillNode, [renderSkillNode, renderNode])
          }
        >
          publish timeout
        </button>
      );
    }

    try {
      const utils = render(<Harness />, {
        container: dom.window.document.body,
      });
      utils.getByRole("button", { name: "publish timeout" }).click();

      await waitFor(() => assert.equal(updates.length, 2));
      assert.equal(updates[1][0].status, "blocked");
      assert.equal(updates[1][1].outputs?.render_status, "timeout");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("ignores an old render response after the same node starts a new job", async () => {
    const originalFetch = globalThis.fetch;
    const updates: ProductionCanvasNode[][] = [];
    const resolvedContexts: ProductionCanvasResolvedContext[] = [];
    const renderResolvers: Array<(response: Response) => void> = [];
    const renderResponse = (renderJobId: number) =>
      new Response(
        JSON.stringify({
          items: [
            {
              id: renderJobId,
              business_id: `render-${renderJobId}`,
              timeline_id: 71,
              timeline_version: renderJobId,
              render_type: "final",
              preset_hash: "preset",
              preset: { fps: 24 },
              status: "succeeded",
              progress: 100,
              output_asset_id: renderJobId + 1000,
              output_asset: {
                id: renderJobId + 1000,
                business_id: `asset-${renderJobId}`,
                asset_type: "video",
                origin: "timeline_render",
                file_url: `/media/${renderJobId}.mp4`,
                created_at: "2026-07-15T10:00:00Z",
                updated_at: "2026-07-15T10:00:00Z",
              },
              created_at: "2026-07-15T10:00:00Z",
              updated_at: "2026-07-15T10:00:01Z",
            },
          ],
        }),
        { headers: { "content-type": "application/json" } },
      );
    globalThis.fetch = async (input) => {
      const url = String(input);
      if (url.includes("/production-canvas/runs/run-a")) {
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              run_id: "run-a",
              task_id: 1,
              nodes: [],
              selected_assets: { virtual_ips: [], environments: [] },
              skill_manifest: { version: "production_canvas.v1" },
            },
          }),
          { headers: { "content-type": "application/json" } },
        );
      }
      if (url === "/api/v1/timelines/71/render-jobs") {
        return new Promise<Response>((resolve) => {
          renderResolvers.push(resolve);
        });
      }
      throw new Error(`Unexpected request ${url}`);
    };

    function Harness() {
      const publish = useProductionCanvasExecutionTracker({
        onDomainContextResolved: (context) => resolvedContexts.push(context),
        onNodesCreated: (nodes) => updates.push(nodes),
        pollIntervalMs: 5,
        maxPollMs: 500,
        runId: "run-a",
      });
      const publishRender = (renderJobId: number) => {
        const skillNode = {
          ...renderSkillNode,
          outputs: {
            canvas_run_id: "run-a",
            timeline_id: 71,
            render_job_id: renderJobId,
            render_status: "queued",
          },
        };
        const evidenceNode = {
          ...renderNode,
          id: `${renderSkillNode.id}-render-${renderJobId}`,
          outputs: {
            canvas_run_id: "run-a",
            source_node_id: renderSkillNode.id,
            timeline_id: 71,
            render_job_id: renderJobId,
            render_status: "queued",
          },
        };
        publish(renderSkillNode, [skillNode, evidenceNode], "run-a");
      };
      return (
        <>
          <button type="button" onClick={() => publishRender(122)}>
            publish old render
          </button>
          <button type="button" onClick={() => publishRender(123)}>
            publish new render
          </button>
        </>
      );
    }

    try {
      const utils = render(<Harness />, {
        container: dom.window.document.body,
      });
      utils.getByRole("button", { name: "publish old render" }).click();
      await waitFor(() => assert.equal(renderResolvers.length, 1));
      utils.getByRole("button", { name: "publish new render" }).click();
      await waitFor(() => assert.equal(renderResolvers.length, 2));
      assert.deepEqual(resolvedContexts, [
        { timeline_id: 71 },
        { timeline_id: 71 },
      ]);
      const baselineContextCount = resolvedContexts.length;
      await act(async () => renderResolvers[0]?.(renderResponse(122)));
      assert.equal(updates.length, 2);
      assert.equal(resolvedContexts.length, baselineContextCount);

      await act(async () => renderResolvers[1]?.(renderResponse(123)));
      await waitFor(() => assert.equal(updates.length, 3));
      assert.equal(updates[2][0].outputs?.render_job_id, 123);
      assert.deepEqual(resolvedContexts, [
        { timeline_id: 71 },
        { timeline_id: 71 },
        { timeline_id: 71, timeline_version: 123 },
      ]);
    } finally {
      for (const resolve of renderResolvers) resolve(renderResponse(123));
      globalThis.fetch = originalFetch;
    }
  });
});
