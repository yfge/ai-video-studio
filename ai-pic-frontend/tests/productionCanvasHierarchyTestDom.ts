import assert from "node:assert/strict";
import { fireEvent, waitFor, within } from "@testing-library/react";
import { JSDOM } from "jsdom";

export const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/canvas",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).Element = dom.window.Element;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).SVGElement = dom.window.SVGElement;
(globalThis as any).localStorage = dom.window.localStorage;
(globalThis as any).Event = dom.window.Event;
(globalThis as any).InputEvent = dom.window.InputEvent;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  configurable: true,
});

export function hierarchyNode(container: HTMLElement, id: string) {
  const node = container.querySelector<HTMLElement>(
    `[data-hierarchy-node="${id}"]`,
  );
  assert.ok(node, `expected hierarchy node ${id}`);
  return node;
}

export function expand(container: HTMLElement, id: string) {
  fireEvent.click(
    within(hierarchyNode(container, id)).getByRole("button", {
      name: /^展开/,
    }),
  );
}

export async function expectNode(container: HTMLElement, id: string) {
  await waitFor(() => assert.ok(hierarchyNode(container, id)));
}
