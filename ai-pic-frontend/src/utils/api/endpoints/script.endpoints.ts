/**
 * Script API endpoints.
 */

export * from "./script/core.endpoints";
export * from "./script/generation.endpoints";
export * from "./script/audio.endpoints";
export * from "./script/storyboard.endpoints";
export * from "./script/storyboard-scene-grid.endpoints";

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
import { generateTimelinePipelineAsync } from "./script/audio.endpoints";
import {
  generateSceneGridSheet,
  generateSceneGridVideo,
  getSceneGrids,
} from "./script/storyboard-scene-grid.endpoints";
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
  generateTimelinePipelineAsync,
  getStoryboard,
  previewStoryboardPrompt,
  generateStoryboard,
  generateStoryboardAsync,
  generateStoryboardVideo,
  generateStoryboardImages,
  updateStoryboard,
  generateSceneGridSheet,
  generateSceneGridVideo,
  getSceneGrids,
};
