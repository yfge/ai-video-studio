/**
 * Script API endpoints.
 */

export * from "./script/core.endpoints";
export * from "./script/generation.endpoints";
export * from "./script/audio.endpoints";
export * from "./script/storyboard.endpoints";

import {
  deleteScript,
  exportScript,
  getEpisodeScripts,
  getScript,
  getScriptFormats,
  getScriptLanguages,
  getScripts,
  regenerateScript,
  updateScript,
} from "./script/core.endpoints";
import {
  generateScript,
  generateScriptAsync,
  previewScriptPrompt,
} from "./script/generation.endpoints";
import {
  generateAudioTimelineAsync,
  generateSceneDialogueAudioAsync,
  generateStoryboardFromAudioTimelineAsync,
  generateTimelinePipelineAsync,
} from "./script/audio.endpoints";
import {
  generateStoryboard,
  generateStoryboardAsync,
  generateStoryboardImages,
  generateStoryboardVideo,
  getStoryboard,
  previewStoryboardPrompt,
  updateStoryboard,
} from "./script/storyboard.endpoints";

/**
 * Script API namespace.
 */
export const scriptAPI = {
  getScripts,
  getScript,
  generateScript,
  generateScriptAsync,
  previewScriptPrompt,
  updateScript,
  deleteScript,
  getEpisodeScripts,
  regenerateScript,
  getScriptFormats,
  getScriptLanguages,
  exportScript,
  generateSceneDialogueAudioAsync,
  generateAudioTimelineAsync,
  generateStoryboardFromAudioTimelineAsync,
  generateTimelinePipelineAsync,
  getStoryboard,
  previewStoryboardPrompt,
  generateStoryboard,
  generateStoryboardAsync,
  generateStoryboardVideo,
  generateStoryboardImages,
  updateStoryboard,
};
