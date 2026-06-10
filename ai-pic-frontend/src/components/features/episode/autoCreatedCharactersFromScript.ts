import type { AutoCreatedCharacter, Script } from "@/utils/api/types";

function isAutoCreatedCharacter(value: unknown): value is AutoCreatedCharacter {
  if (!value || typeof value !== "object") return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.character_name === "string" &&
    typeof record.episode_character_id === "number"
  );
}

/**
 * Read the auto-created temporary characters persisted by script generation
 * into script.extra_metadata, so the characters tab can surface the binding
 * reminder for both sync and async generation paths.
 */
export function autoCreatedCharactersFromScript(
  script: Script | null,
): AutoCreatedCharacter[] {
  const meta = script?.extra_metadata;
  if (!meta || typeof meta !== "object") return [];
  const raw = (meta as Record<string, unknown>)["auto_created_characters"];
  if (!Array.isArray(raw)) return [];
  return raw.filter(isAutoCreatedCharacter);
}
