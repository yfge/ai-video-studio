import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { cleanup, render } from "@testing-library/react";
import { JSDOM } from "jsdom";

import {
  OperatorShellNavIcon,
  type OperatorNavIconName,
} from "../src/components/shared/operator/OperatorShellNavIcon";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;

const iconNames: OperatorNavIconName[] = [
  "workspace",
  "canvas",
  "ip",
  "stories",
  "environments",
  "tasks",
  "users",
  "stats",
  "settings",
];

describe("OperatorShellNavIcon", () => {
  afterEach(() => cleanup());

  it("renders navigation icons without visible placeholder letters", () => {
    for (const name of iconNames) {
      const utils = render(
        <OperatorShellNavIcon name={name} className="h-4 w-4" />,
        { container: dom.window.document.body },
      );
      const svg = utils.container.querySelector("svg");
      assert.ok(svg);
      assert.equal(svg.getAttribute("aria-hidden"), "true");
      assert.equal(svg.textContent, "");
      cleanup();
    }
  });
});
