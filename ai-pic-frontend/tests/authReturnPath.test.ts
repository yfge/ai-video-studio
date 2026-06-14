import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  buildLoginPathForReturn,
  resolveSafeLoginReturnPath,
} from "../src/utils/authReturnPath";

describe("auth return path helpers", () => {
  it("preserves internal workspace deep links when redirecting to login", () => {
    const target =
      "/episodes/12c6/workspace?tab=timeline&scriptId=143&clipId=video_scene_580_beat_3923_001";

    assert.equal(
      buildLoginPathForReturn(target),
      `/login?next=${encodeURIComponent(target)}`,
    );
    assert.equal(resolveSafeLoginReturnPath(target), target);
  });

  it("rejects external or login-loop return paths", () => {
    assert.equal(resolveSafeLoginReturnPath("https://evil.example/path"), "/");
    assert.equal(resolveSafeLoginReturnPath("//evil.example/path"), "/");
    assert.equal(resolveSafeLoginReturnPath("/login?next=/episodes/1"), "/");
    assert.equal(resolveSafeLoginReturnPath(""), "/");
  });
});
