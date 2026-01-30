/**
 * Story Structure API endpoints (scenes, beats, shots, environments).
 */

export * from "./story-structure/scenes.endpoints";
export * from "./story-structure/beats.endpoints";
export * from "./story-structure/shots.endpoints";
export * from "./story-structure/treatments.endpoints";
export * from "./story-structure/environments.endpoints";

import {
  createScene,
  deleteScene,
  getNormalizedScenes,
  updateScene,
} from "./story-structure/scenes.endpoints";
import {
  createSceneBeat,
  deleteSceneBeat,
  getNormalizedSceneBeats,
  updateSceneBeat,
} from "./story-structure/beats.endpoints";
import {
  createSceneShot,
  deleteSceneShot,
  getNormalizedSceneShots,
  updateSceneShot,
} from "./story-structure/shots.endpoints";
import {
  createStoryTreatment,
  getStoryTreatments,
} from "./story-structure/treatments.endpoints";
import {
  createEnvironment,
  deleteEnvironment,
  deleteEnvironmentImage,
  generateEnvironmentImages,
  generateEnvironmentImagesAsync,
  generateEnvironmentImageVariants,
  generateEnvironmentImageVariantsAsync,
  getEnvironment,
  listEnvironmentImages,
  listEnvironments,
  updateEnvironment,
  uploadEnvironmentImage,
} from "./story-structure/environments.endpoints";

/**
 * Story Structure API namespace.
 */
export const storyStructureAPI = {
  // Scenes
  getNormalizedScenes,
  createScene,
  updateScene,
  deleteScene,
  // Beats
  getNormalizedSceneBeats,
  createSceneBeat,
  updateSceneBeat,
  deleteSceneBeat,
  // Shots
  getNormalizedSceneShots,
  createSceneShot,
  updateSceneShot,
  deleteSceneShot,
  // Treatments
  getStoryTreatments,
  createStoryTreatment,
  // Environments
  listEnvironments,
  getEnvironment,
  createEnvironment,
  updateEnvironment,
  deleteEnvironment,
  listEnvironmentImages,
  uploadEnvironmentImage,
  generateEnvironmentImages,
  generateEnvironmentImageVariants,
  generateEnvironmentImagesAsync,
  generateEnvironmentImageVariantsAsync,
  deleteEnvironmentImage,
};
