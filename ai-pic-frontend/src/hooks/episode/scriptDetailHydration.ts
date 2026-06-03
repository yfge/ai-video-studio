import type { Script } from "@/utils/api/types";

export function scriptNeedsDetail(script: Script | null): boolean {
  if (!script?.id) return false;
  return (
    !script.content ||
    !Array.isArray(script.scenes) ||
    !Array.isArray(script.dialogues) ||
    !Array.isArray(script.stage_directions)
  );
}

export function mergeScriptDetail(scripts: Script[], detail: Script): Script[] {
  let found = false;
  const merged = scripts.map((script) => {
    if (script.id !== detail.id) return script;
    found = true;
    return { ...script, ...detail };
  });
  return found ? merged : [detail, ...merged];
}
