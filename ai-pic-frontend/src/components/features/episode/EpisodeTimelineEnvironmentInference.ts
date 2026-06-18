import type { Environment, NormalizedScene } from "@/utils/api/types";

const LOCATION_TOKENS = [
  "老拐",
  "阿盖儿",
  "客厅",
  "厨房",
  "餐厅",
  "工作室",
  "办公室",
  "会议室",
  "公寓",
  "家",
];

const HOME_ROOM_TOKENS = ["客厅", "厨房", "餐厅", "卧室"];

export function inferEnvironmentIdForScene(
  scene: NormalizedScene | null,
  environments: Environment[],
) {
  if (!scene || typeof scene.environment_id === "number") {
    return scene?.environment_id ?? null;
  }
  const sceneText = normalizedText([
    scene.slug_line,
    scene.location,
    scene.summary,
    scene.environment_type,
  ]);
  if (!sceneText) return null;
  const scored = environments
    .map((environment) => ({
      id: environment.id,
      score: scoreEnvironmentMatch(sceneText, environment),
    }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score);
  return scored[0]?.id ?? null;
}

function scoreEnvironmentMatch(sceneText: string, environment: Environment) {
  const envName = normalizedText([environment.name]);
  const envText = normalizedText([environment.name, environment.description]);
  if (!envText) return 0;
  let score = 0;
  if (envName && (sceneText.includes(envName) || envName.includes(sceneText))) {
    score += 100;
  }
  for (const token of LOCATION_TOKENS) {
    if (sceneText.includes(token) && envText.includes(token)) {
      score += token === "工作室" ? 50 : 30;
    }
  }
  if (
    HOME_ROOM_TOKENS.some((token) => sceneText.includes(token)) &&
    envText.includes("家")
  ) {
    score += 25;
  }
  return score;
}

function normalizedText(values: unknown[]) {
  return values
    .filter((value): value is string => typeof value === "string")
    .map((value) => value.trim().toLocaleLowerCase())
    .filter(Boolean)
    .join(" ");
}
