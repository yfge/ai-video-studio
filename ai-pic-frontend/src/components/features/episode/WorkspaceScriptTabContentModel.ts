import type { NormalizedScene } from "@/utils/api/types";
import type { SceneNode } from "../SceneStructurePanel";

export type ScriptScene = {
  scene_number?: number | string;
  location?: string;
  time?: string;
  description?: string;
  characters?: string[] | string;
  notes?: string;
  [key: string]: unknown;
};

export type ScriptDialogue =
  | {
      scene_number?: number | string;
      character?: string;
      content?: string;
      emotion?: string;
      action?: string;
    }
  | string;

export type ScriptDirection =
  | {
      scene_number?: number | string;
      timing?: string;
      content?: string;
      type?: string;
    }
  | string;

export const toSceneNumber = (
  value: number | string | undefined,
): number | undefined => {
  if (typeof value === "number") return value;
  if (typeof value === "string") {
    const parsed = parseInt(value, 10);
    return Number.isNaN(parsed) ? undefined : parsed;
  }
  return undefined;
};

export const normalizeScenes = (scenes: unknown): ScriptScene[] => {
  if (!Array.isArray(scenes)) return [];
  return scenes.map((scene, index) => {
    if (scene && typeof scene === "object") return scene as ScriptScene;
    return {
      scene_number: index + 1,
      description: typeof scene === "string" ? scene : undefined,
    };
  });
};

export const normalizeDialogues = (items: unknown): ScriptDialogue[] =>
  Array.isArray(items) ? (items as ScriptDialogue[]) : [];

export const normalizeDirections = (items: unknown): ScriptDirection[] =>
  Array.isArray(items) ? (items as ScriptDirection[]) : [];

export const sceneNodesFromNormalizedScenes = (
  scenes: NormalizedScene[],
): SceneNode[] =>
  scenes.map((scene) => ({
    id: scene.id,
    scene_number: scene.scene_number,
    slug_line: scene.slug_line,
    location: scene.location ?? undefined,
    time_of_day: scene.time_of_day ?? undefined,
    status: scene.status,
    beats: [],
    shots: [],
  }));

export const sceneViewsFromNodes = (scenes: SceneNode[]): ScriptScene[] =>
  scenes.map((scene, index) => ({
    scene_number: toSceneNumber(scene.scene_number) ?? index + 1,
    location: scene.location,
    time: scene.time_of_day,
    description:
      scene.slug_line || scene.status || `场景 ${scene.scene_number}`,
  }));
