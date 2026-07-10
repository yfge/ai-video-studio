import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";
import { AppRouterContext } from "next/dist/shared/lib/app-router-context.shared-runtime";
import { PathnameContext } from "next/dist/shared/lib/hooks-client-context.shared-runtime";

import { AlertModalProvider } from "../src/components/shared/modals/AlertModalProvider";
import { TasksPage } from "../src/components/features/tasks/TasksPage";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/tasks?task_id=77",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).localStorage = dom.window.localStorage;
(globalThis as any).Event = dom.window.Event;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

const router = {
  back() {},
  forward() {},
  refresh() {},
  hmrRefresh() {},
  push() {},
  replace() {},
  prefetch() {},
};

describe("TasksPage deep link", () => {
  afterEach(() => cleanup());

  it("loads and highlights a linked canvas task", async () => {
    const originalFetch = globalThis.fetch;
    const requests: string[] = [];
    globalThis.fetch = async (input) => {
      requests.push(String(input));
      return new Response(
        JSON.stringify({
          success: true,
          data: {
            id: 77,
            business_id: "task-77",
            title: "已提交现有剧本生成任务",
            task_type: "script_generation",
            status: "pending",
            created_at: "2026-07-02T00:00:00Z",
            user_id: 1,
            parameters: {},
          },
        }),
        { headers: { "content-type": "application/json" } },
      );
    };

    try {
      const utils = render(
        <AppRouterContext.Provider value={router}>
          <PathnameContext.Provider value="/tasks">
            <AlertModalProvider>
              <TasksPage targetTaskId={77} />
            </AlertModalProvider>
          </PathnameContext.Provider>
        </AppRouterContext.Provider>,
        { container: dom.window.document.body },
      );

      await waitFor(() => assert.ok(utils.getByText("已提交现有剧本生成任务")));

      assert.ok(requests[0]?.endsWith("/api/v1/tasks/77"));
      assert.ok(utils.getByText("正在查看任务 #77"));
      assert.ok(utils.container.querySelector("[data-focused-task='true']"));
      await waitFor(() => assert.ok(utils.getByText("任务ID：77")));
      assert.equal(
        utils.getByRole("link", { name: "查看全部任务" }).getAttribute("href"),
        "/tasks",
      );
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
