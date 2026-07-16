import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { useEffect } from "react";
import { act, cleanup, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";
import { useProductionCanvasTaskSync } from "../src/components/features/canvas/useProductionCanvasTaskSync";
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

function taskNode(runId: string, taskId: number): ProductionCanvasNode {
  return {
    id: "shared-task-node",
    kind: "note",
    label: `Task #${taskId}`,
    title: `Run ${runId} task`,
    status: "running",
    x: 0,
    y: 0,
    width: 220,
    outputs: {
      canvas_run_id: runId,
      source_node_id: "shared-source-node",
      task_id: taskId,
    },
  };
}

function sourceNode(runId: string, taskId: number): ProductionCanvasNode {
  return {
    id: "shared-source-node",
    label: "Script",
    title: "Script",
    status: "running",
    x: 0,
    y: 100,
    width: 220,
    skill: "script.generate",
    outputs: { canvas_run_id: runId, dispatched_task_id: taskId },
  };
}

function completedTask(taskId: number, scriptId: number) {
  return new Response(
    JSON.stringify({
      id: taskId,
      business_id: `task-${taskId}`,
      title: `Task ${taskId} completed`,
      status: "completed",
      result_context: { script_id: scriptId },
      created_at: "2026-07-15T10:00:00Z",
      user_id: 1,
    }),
    { headers: { "content-type": "application/json" } },
  );
}

describe("useProductionCanvasTaskSync run isolation", () => {
  afterEach(() => cleanup());

  it("drops Run A refresh and reports only the new Run B context", async () => {
    const originalFetch = globalThis.fetch;
    const patches: Array<{
      nodeId: string;
      patch: Partial<ProductionCanvasNode>;
    }> = [];
    const contexts: ProductionCanvasResolvedContext[] = [];
    let resolveA: ((response: Response) => void) | undefined;
    let resolveB: ((response: Response) => void) | undefined;
    let refreshTask:
      | ((node: ProductionCanvasNode) => Promise<void>)
      | undefined;
    globalThis.fetch = async (input) => {
      const url = String(input);
      if (url.endsWith("/101")) {
        return new Promise<Response>((resolve) => {
          resolveA = resolve;
        });
      }
      if (url.endsWith("/202")) {
        return new Promise<Response>((resolve) => {
          resolveB = resolve;
        });
      }
      throw new Error(`Unexpected request ${url}`);
    };

    function Harness({ runId, taskId }: { runId: string; taskId: number }) {
      const sync = useProductionCanvasTaskSync({
        currentRunId: runId,
        getCurrentRunId: () => runId,
        nodes: [sourceNode(runId, taskId), taskNode(runId, taskId)],
        onDomainContextResolved: (context) => contexts.push(context),
        onNodeUpdated: (nodeId, patch) => patches.push({ nodeId, patch }),
      });
      useEffect(() => {
        refreshTask = sync.refreshTaskNode;
      });
      return (
        <button
          type="button"
          onClick={() => void sync.refreshTaskNode(taskNode(runId, taskId))}
        >
          refresh {runId}
        </button>
      );
    }

    try {
      const utils = render(<Harness runId="run-a" taskId={101} />, {
        container: dom.window.document.body,
      });
      act(() => void refreshTask?.(taskNode("run-a", 101)));
      await waitFor(() => assert.ok(resolveA));

      utils.rerender(<Harness runId="run-b" taskId={202} />);
      act(() => void refreshTask?.(taskNode("run-b", 202)));
      await waitFor(() => assert.ok(resolveB));
      await act(async () => {
        resolveA?.(completedTask(101, 301));
        await new Promise((resolve) => setTimeout(resolve, 0));
      });
      assert.deepEqual(patches, []);
      assert.deepEqual(contexts, []);

      await act(async () => resolveB?.(completedTask(202, 302)));
      await waitFor(() => assert.equal(patches.length, 2));
      const sourcePatch = patches.find(
        (item) => item.nodeId === "shared-source-node",
      );
      assert.equal(sourcePatch?.patch.outputs?.task_id, 202);
      assert.equal(sourcePatch?.patch.outputs?.script_id, 302);
      assert.deepEqual(contexts, [{ script_id: 302, task_id: 202 }]);
    } finally {
      resolveA?.(completedTask(101, 301));
      resolveB?.(completedTask(202, 302));
      globalThis.fetch = originalFetch;
    }
  });

  it("drops a late task refresh after a null-Run canvas reset", async () => {
    const originalFetch = globalThis.fetch;
    const patches: unknown[] = [];
    const contexts: ProductionCanvasResolvedContext[] = [];
    let resolveTask: ((response: Response) => void) | undefined;
    globalThis.fetch = async () =>
      new Promise<Response>((resolve) => {
        resolveTask = resolve;
      });

    function Harness({ epoch }: { epoch: number }) {
      const sync = useProductionCanvasTaskSync({
        captureStateIdentity: () => ({ runId: "", epoch }),
        currentRunId: null,
        getCurrentRunId: () => null,
        onDomainContextResolved: (context) => contexts.push(context),
        onNodeUpdated: (nodeId, patch) => patches.push({ nodeId, patch }),
      });
      return (
        <button
          type="button"
          onClick={() => void sync.refreshTaskNode(taskNode("", 101))}
        >
          refresh fresh
        </button>
      );
    }

    try {
      const utils = render(<Harness epoch={0} />, {
        container: dom.window.document.body,
      });
      utils.getByRole("button", { name: "refresh fresh" }).click();
      await waitFor(() => assert.ok(resolveTask));
      utils.rerender(<Harness epoch={1} />);
      await act(async () => resolveTask?.(completedTask(101, 301)));
      assert.deepEqual(patches, []);
      assert.deepEqual(contexts, []);
    } finally {
      resolveTask?.(completedTask(101, 301));
      globalThis.fetch = originalFetch;
    }
  });

  it("drops a late refresh when the same Run node now points at a newer Task", async () => {
    const originalFetch = globalThis.fetch;
    const patches: unknown[] = [];
    const contexts: ProductionCanvasResolvedContext[] = [];
    let resolveOldTask: ((response: Response) => void) | undefined;
    globalThis.fetch = async () =>
      new Promise<Response>((resolve) => {
        resolveOldTask = resolve;
      });

    function Harness({ taskId }: { taskId: number }) {
      const sync = useProductionCanvasTaskSync({
        currentRunId: "run-a",
        getCurrentRunId: () => "run-a",
        nodes: [sourceNode("run-a", taskId), taskNode("run-a", taskId)],
        onDomainContextResolved: (context) => contexts.push(context),
        onNodeUpdated: (nodeId, patch) => patches.push({ nodeId, patch }),
      });
      return (
        <button
          type="button"
          onClick={() => void sync.refreshTaskNode(taskNode("run-a", taskId))}
        >
          refresh task {taskId}
        </button>
      );
    }

    try {
      const utils = render(<Harness taskId={700} />, {
        container: dom.window.document.body,
      });
      utils.getByRole("button", { name: "refresh task 700" }).click();
      await waitFor(() => assert.ok(resolveOldTask));

      utils.rerender(<Harness taskId={701} />);
      await act(async () => resolveOldTask?.(completedTask(700, 370)));

      assert.deepEqual(patches, []);
      assert.deepEqual(contexts, []);
    } finally {
      resolveOldTask?.(completedTask(700, 370));
      globalThis.fetch = originalFetch;
    }
  });

  it("keeps a scoped image Task on its own Timeline without publishing global context", async () => {
    const originalFetch = globalThis.fetch;
    const patches: Array<Partial<ProductionCanvasNode>> = [];
    const contexts: ProductionCanvasResolvedContext[] = [];
    const node: ProductionCanvasNode = {
      ...taskNode("run-a", 303),
      outputs: {
        canvas_run_id: "run-a",
        task_id: 303,
        source_node_id: "image-a",
        skill: "image.candidates",
        queued_frame_indexes: [0],
        script_id: 140,
        timeline_id: 501,
        timeline_version: 7,
        clip_id: "clip-b",
      },
    };
    globalThis.fetch = async () =>
      new Response(
        JSON.stringify({
          id: 303,
          business_id: "task-303",
          title: "Image completed",
          status: "completed",
          result_context: {
            script_id: 301,
            timeline_id: 502,
            timeline_version: 1,
            clip_id: "clip-global",
          },
          created_at: "2026-07-15T10:00:00Z",
          user_id: 1,
        }),
        { headers: { "content-type": "application/json" } },
      );

    function Harness() {
      const source: ProductionCanvasNode = {
        ...sourceNode("run-a", 303),
        id: "image-a",
        skill: "image.candidates",
        outputs: {
          canvas_run_id: "run-a",
          dispatched_task_id: 303,
          frame_indexes: [0],
          script_id: 140,
          timeline_id: 501,
          timeline_version: 7,
          clip_id: "clip-b",
        },
      };
      const sync = useProductionCanvasTaskSync({
        currentRunId: "run-a",
        getCurrentRunId: () => "run-a",
        nodes: [source, node],
        onDomainContextResolved: (context) => contexts.push(context),
        onNodeUpdated: (_nodeId, patch) => patches.push(patch),
      });
      return (
        <button type="button" onClick={() => void sync.refreshTaskNode(node)}>
          refresh scoped
        </button>
      );
    }

    try {
      const utils = render(<Harness />, {
        container: dom.window.document.body,
      });
      utils.getByRole("button", { name: "refresh scoped" }).click();
      await waitFor(() => assert.equal(patches.length, 2));
      for (const patch of patches) {
        assert.equal(patch.outputs?.script_id, 140);
        assert.equal(patch.outputs?.timeline_id, 501);
        assert.equal(patch.outputs?.timeline_version, 7);
        assert.equal(patch.outputs?.clip_id, "clip-b");
        assert.equal(patch.outputs?.task_status, "completed");
      }
      assert.deepEqual(contexts, []);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
