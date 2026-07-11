import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import React from "react";
import {
  act,
  cleanup,
  fireEvent,
  render,
  waitFor,
} from "@testing-library/react";
import { JSDOM } from "jsdom";

import {
  ToastProvider,
  useToast,
} from "../src/components/shared/notifications";
import type { NotifyVariant } from "../src/components/shared/notifications";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).localStorage = dom.window.localStorage;

function Harness({
  onReady,
}: {
  onReady: (
    notify: (
      message: string,
      variant?: NotifyVariant,
      options?: { durationMs?: number; title?: string },
    ) => void,
  ) => void;
}) {
  const { notify } = useToast();
  onReady(notify);
  return null;
}

function renderToastHarness() {
  let notifyFn:
    | ((
        message: string,
        variant?: NotifyVariant,
        options?: { durationMs?: number; title?: string },
      ) => void)
    | null = null;
  const utils = render(
    React.createElement(
      ToastProvider,
      null,
      React.createElement(Harness, {
        onReady: (notify) => {
          notifyFn = notify;
        },
      }),
    ),
    { container: dom.window.document.body },
  );
  assert.ok(notifyFn);
  return { utils, notify: notifyFn! };
}

describe("toast provider", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders success toasts as status and errors as alert", async () => {
    const { utils, notify } = renderToastHarness();
    notify("剧本生成任务已提交", "success");
    notify("生成失败：余额不足", "error");

    await waitFor(() => {
      assert.ok(utils.getByText("剧本生成任务已提交"));
      assert.ok(utils.getByText("生成失败：余额不足"));
    });
    const statuses = utils.getAllByRole("status");
    const alerts = utils.getAllByRole("alert");
    assert.equal(statuses.length, 1);
    assert.equal(alerts.length, 1);
  });

  it("auto-dismisses after the configured duration", async () => {
    const { utils, notify } = renderToastHarness();
    notify("短暂提示", "info", { durationMs: 30 });
    await waitFor(() => assert.ok(utils.getByText("短暂提示")));
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 60));
    });
    assert.equal(utils.queryByText("短暂提示"), null);
  });

  it("dismisses on manual close", async () => {
    const { utils, notify } = renderToastHarness();
    notify("手动关闭我", "warning", { durationMs: 60000 });
    await waitFor(() => assert.ok(utils.getByText("手动关闭我")));
    fireEvent.click(utils.getByLabelText("关闭通知"));
    await waitFor(() => assert.equal(utils.queryByText("手动关闭我"), null));
  });

  it("caps the visible stack at five toasts", async () => {
    const { utils, notify } = renderToastHarness();
    for (let index = 1; index <= 7; index++) {
      notify(`提示 ${index}`, "info", { durationMs: 60000 });
    }
    await waitFor(() => assert.ok(utils.getByText("提示 7")));
    assert.equal(utils.getAllByRole("status").length, 5);
    assert.equal(utils.queryByText("提示 1"), null);
    assert.equal(utils.queryByText("提示 2"), null);
  });

  it("renders an optional title", async () => {
    const { utils, notify } = renderToastHarness();
    notify("成片已就绪", "success", { title: "渲染完成", durationMs: 60000 });
    await waitFor(() => {
      assert.ok(utils.getByText("渲染完成"));
      assert.ok(utils.getByText("成片已就绪"));
    });
  });
});
