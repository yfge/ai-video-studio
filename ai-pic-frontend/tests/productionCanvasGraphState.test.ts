import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  removeProductionCanvasNode,
  updateProductionCanvasNode,
} from "../src/components/features/canvas/productionCanvasGraphState";

describe("productionCanvasGraphState", () => {
  it("removes a node and its connected edges", () => {
    const result = removeProductionCanvasNode(
      [
        {
          id: "a",
          label: "A",
          title: "A",
          status: "review",
          x: 0,
          y: 0,
          width: 1,
        },
        {
          id: "b",
          label: "B",
          title: "B",
          status: "review",
          x: 0,
          y: 0,
          width: 1,
        },
        {
          id: "c",
          label: "C",
          title: "C",
          status: "review",
          x: 0,
          y: 0,
          width: 1,
        },
      ],
      [
        { from: "a", to: "b" },
        { from: "b", to: "c" },
        { from: "a", to: "c" },
      ],
      "b",
    );

    assert.deepEqual(
      result.nodes.map((node) => node.id),
      ["a", "c"],
    );
    assert.deepEqual(result.edges, [{ from: "a", to: "c" }]);
  });

  it("merges node outputs and removes undefined output keys", () => {
    const [node] = updateProductionCanvasNode(
      [
        {
          id: "a",
          label: "A",
          title: "A",
          status: "review",
          x: 0,
          y: 0,
          width: 1,
          outputs: { keep: 1, remove: 2 },
        },
      ],
      "a",
      { title: "Updated", outputs: { remove: undefined, add: 3 } },
    );

    assert.equal(node?.title, "Updated");
    assert.deepEqual(node?.outputs, { keep: 1, add: 3 });
  });
});
