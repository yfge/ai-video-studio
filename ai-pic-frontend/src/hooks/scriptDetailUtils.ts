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

export const formatDate = (value?: string): string => {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
};

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
    if (scene && typeof scene === "object") {
      return scene as ScriptScene;
    }
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
