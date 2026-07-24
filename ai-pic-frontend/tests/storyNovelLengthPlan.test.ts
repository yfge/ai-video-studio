import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  applyRangeToChapters,
  chapterLength,
  plannedLengthTotals,
  validateLengthOverrides,
  validateLengthRange,
} from "../src/components/features/story-detail/storyNovelLengthPlan";

const defaults = {
  min_chars: 3000,
  target_chars: 4000,
  max_chars: 5000,
};

describe("novel length plan", () => {
  it("inherits profile defaults and applies an isolated chapter override", () => {
    const overrides = {
      "2": { min_chars: 3800, target_chars: 4600, max_chars: 5200 },
    };
    assert.equal(
      chapterLength(1, defaults, overrides).source,
      "profile_default",
    );
    assert.equal(
      chapterLength(2, defaults, overrides).source,
      "chapter_override",
    );
    assert.deepEqual(plannedLengthTotals([1, 2, 3], defaults, overrides), {
      min_chars: 9800,
      target_chars: 12600,
      max_chars: 15200,
    });
  });

  it("supports bulk application, missing-only application, and no total cap", () => {
    const range = { min_chars: 1, target_chars: 2, max_chars: 3 };
    const first = applyRangeToChapters([1, 2], {}, range);
    const missingOnly = applyRangeToChapters(
      [1, 2, 3],
      { ...first, "2": defaults },
      range,
      true,
    );
    assert.deepEqual(missingOnly["2"], defaults);
    assert.deepEqual(missingOnly["3"], range);
    assert.equal(
      plannedLengthTotals(
        Array.from({ length: 1000 }, (_, index) => index + 1),
        defaults,
        {},
      ).target_chars,
      4_000_000,
    );
  });

  it("rejects non-integer and inverted ranges", () => {
    assert.equal(validateLengthRange(defaults), null);
    assert.match(
      validateLengthRange({ min_chars: 5, target_chars: 4, max_chars: 3 }) ||
        "",
      /最小值/,
    );
    assert.match(
      validateLengthOverrides({
        "7": { min_chars: 1, target_chars: 1.5, max_chars: 2 },
      }) || "",
      /第 7 章/,
    );
  });
});
