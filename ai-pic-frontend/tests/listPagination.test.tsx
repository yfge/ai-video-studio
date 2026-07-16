import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render } from "@testing-library/react";
import { JSDOM } from "jsdom";
import React from "react";

import { EnvironmentList } from "../src/components/features/environments/EnvironmentList";
import { OperatorPagination } from "../src/components/shared/operator/OperatorPagination";
import { paginateItems } from "../src/hooks/useListPagination";
import { fetchAllPages } from "../src/utils/api/pagination";
import type { Environment } from "../src/utils/api/types";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;

describe("shared list pagination", () => {
  afterEach(() => cleanup());

  it("loads every API page before paginating the visible list", async () => {
    const source = Array.from({ length: 205 }, (_, index) => index + 1);
    const calls: number[] = [];
    const items = await fetchAllPages(async (skip, limit) => {
      calls.push(skip);
      return {
        success: true,
        data: source.slice(skip, skip + limit),
      };
    });

    assert.deepEqual(calls, [0, 100, 200]);
    assert.deepEqual(paginateItems(items, 2, 12), source.slice(12, 24));
  });

  it("uses the same previous and next controls for list pages", () => {
    const requested: number[] = [];
    const utils = render(
      <OperatorPagination
        page={2}
        pageSize={12}
        total={30}
        totalPages={3}
        onPageChange={(page) => requested.push(page)}
        itemLabel="项目"
      />,
      { container: dom.window.document.body },
    );

    fireEvent.click(utils.getByRole("button", { name: "上一页" }));
    fireEvent.click(utils.getByRole("button", { name: "下一页" }));

    assert.deepEqual(requested, [1, 3]);
    assert.ok(utils.getByText("共 30 个项目 · 每页 12 个 · 第 2 / 3 页"));
  });

  it("shows the shared pagination footer on the environment list", () => {
    const environments = Array.from({ length: 12 }, (_, index) => ({
      id: index + 1,
      name: `环境 ${index + 1}`,
      created_at: "2026-07-16T00:00:00Z",
      updated_at: "2026-07-16T00:00:00Z",
    })) satisfies Environment[];
    const utils = render(
      <EnvironmentList
        loading={false}
        list={environments}
        onRefresh={() => undefined}
        onManage={() => undefined}
        onDelete={() => undefined}
        pagination={{
          page: 1,
          pageSize: 12,
          total: 25,
          totalPages: 3,
          onPageChange: () => undefined,
        }}
      />,
      { container: dom.window.document.body },
    );

    assert.equal(utils.getAllByRole("article").length, 12);
    assert.ok(utils.getByText("共 25 个环境资产 · 每页 12 个 · 第 1 / 3 页"));
  });
});
