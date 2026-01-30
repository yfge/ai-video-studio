import { describe, it, afterEach } from "node:test";
import assert from "node:assert";
import React from "react";
import { render, cleanup } from "@testing-library/react";
import { JSDOM } from "jsdom";
import { FrameCard } from "../src/components/features/StoryboardFrameCard";

const dom = new JSDOM("<!doctype html><html><body></body></html>");
(globalThis as any).window = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;

describe("Storyboard frames align to structured beats/shots (UI badge)", () => {
  afterEach(() => cleanup());

  it("renders beat/shot identifiers when present", () => {
    const frame = {
      frame_number: 1,
      description: "A test frame",
      beat_id: 5,
      shot_id: 7,
      shot_number: "1A",
      shot_type: "WS",
    };

    const { getByText } = render(<FrameCard frame={frame} />);

    assert.ok(getByText(/镜头号 1A/));
    assert.ok(getByText(/镜头ID 7/));
    assert.ok(getByText(/节拍 #5/));
    assert.ok(getByText(/WS/));
  });
});
