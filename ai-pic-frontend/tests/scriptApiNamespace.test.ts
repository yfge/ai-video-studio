import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { scriptAPI } from "../src/utils/api/endpoints/script.endpoints";
import {
  generateAudioTimelineAsync,
  generateSceneDialogueAudioAsync,
  generateStoryboardFromAudioTimelineAsync,
} from "../src/utils/api/endpoints/script/audio.endpoints";

describe("script API namespace", () => {
  it("keeps deprecated step-by-step endpoints out of the default UI API", () => {
    assert.equal("generateTimelinePipelineAsync" in scriptAPI, true);
    assert.equal("generateSceneDialogueAudioAsync" in scriptAPI, false);
    assert.equal("generateAudioTimelineAsync" in scriptAPI, false);
    assert.equal(
      "generateStoryboardFromAudioTimelineAsync" in scriptAPI,
      false,
    );
  });

  it("keeps legacy step-by-step functions as named compatibility exports", () => {
    assert.equal(typeof generateSceneDialogueAudioAsync, "function");
    assert.equal(typeof generateAudioTimelineAsync, "function");
    assert.equal(typeof generateStoryboardFromAudioTimelineAsync, "function");
  });
});
