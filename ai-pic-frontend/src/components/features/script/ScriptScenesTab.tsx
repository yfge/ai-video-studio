"use client";

import type { NormalizedScene, NormalizedShot, SceneBeat, Script } from "@/utils/api";
import type { ScriptScene, ScriptDialogue, ScriptDirection } from "@/hooks/useScriptDetail";
import { toSceneNumber } from "@/hooks/useScriptDetail";
import { SceneStructurePanel, type SceneNode } from "@/components/features";
import { SceneTag, formatText } from "@/components/features/StoryboardFrameCard";

interface ScriptScenesTabProps {
  script: Script;
  scenes: ScriptScene[];
  dialogues: ScriptDialogue[];
  directions: ScriptDirection[];
  focusedScene: number | null;
  setFocusedScene: (scene: number) => void;
  activeScene: ScriptScene | null;
  selectedNormalizedScene: NormalizedScene | undefined;
  sceneBeats: SceneBeat[] | undefined;
  sceneShots: NormalizedShot[] | undefined;
  structureLoading: boolean;
  structureError: string | null;
  showStructureEditor: boolean;
  setShowStructureEditor: (show: boolean) => void;
  canEditStructure: boolean;
  setStructuredScenes: (scenes: SceneNode[]) => void;
}

export function ScriptScenesTab({
  script,
  scenes,
  dialogues,
  directions,
  focusedScene,
  setFocusedScene,
  activeScene,
  selectedNormalizedScene,
  sceneBeats,
  sceneShots,
  structureLoading,
  structureError,
  showStructureEditor,
  setShowStructureEditor,
  canEditStructure,
  setStructuredScenes,
}: ScriptScenesTabProps) {
  return (
    <Section title="Scene Details" description="Select scene on left, view structure and text on right">
      <div className="grid gap-4 p-6 lg:grid-cols-[260px,1fr]">
        <div className="space-y-2">
          {scenes.length === 0 && <p className="text-sm text-gray-500">No structured scene info.</p>}
          {scenes.map((scene, idx) => {
            const sceneNumber = toSceneNumber(scene.scene_number) ?? idx + 1;
            const isActive = focusedScene === sceneNumber;
            return (
              <button
                key={`scene-nav-${sceneNumber}`}
                onClick={() => setFocusedScene(sceneNumber)}
                className={`w-full rounded-lg border px-3 py-2 text-left text-sm transition ${
                  isActive
                    ? "border-blue-600 bg-blue-50 text-blue-700"
                    : "border-gray-200 bg-white text-gray-600 hover:border-blue-200"
                }`}
              >
                <div className="font-medium">Scene {sceneNumber}</div>
                <div className="text-xs text-gray-500">{formatText(scene.description, "No description", 60)}</div>
              </button>
            );
          })}
        </div>
        <div className="space-y-4">
          <div className="rounded-lg border border-gray-100 bg-white p-4">
            <SceneDetails scene={activeScene || scenes[0] || null} dialogues={dialogues} directions={directions} />
          </div>
          <div className="rounded-lg border border-gray-100 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-gray-800">Structured Info</h3>
                <p className="text-xs text-gray-500">
                  Beats {sceneBeats?.length ?? 0} · Shots {sceneShots?.length ?? 0}
                  {structureLoading ? " · Loading..." : ""}
                  {structureError ? ` · ${structureError}` : ""}
                </p>
              </div>
              <button
                onClick={() => setShowStructureEditor(!showStructureEditor)}
                className="rounded-full border border-gray-200 px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50"
              >
                {showStructureEditor ? "Hide Editor" : "Edit Structure"}
              </button>
            </div>
            {selectedNormalizedScene ? (
              <>
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  <div className="rounded border border-gray-100 bg-gray-50 p-3">
                    <div className="text-xs font-semibold text-gray-600">Beats</div>
                    <div className="mt-1 space-y-1 text-xs text-gray-700">
                      {(sceneBeats ?? []).length === 0 && <div className="text-gray-400">No beats</div>}
                      {(sceneBeats ?? []).slice(0, 5).map((beat) => (
                        <div key={beat.id} className="rounded bg-white px-2 py-1 shadow-sm">
                          <span className="font-medium">#{beat.order_index}</span>{" "}
                          <span className="text-gray-600">{beat.beat_summary || beat.dialogue_excerpt || "—"}</span>
                        </div>
                      ))}
                      {(sceneBeats ?? []).length > 5 && (
                        <div className="text-[11px] text-gray-500">Showing first 5</div>
                      )}
                    </div>
                  </div>
                  <div className="rounded border border-gray-100 bg-gray-50 p-3">
                    <div className="text-xs font-semibold text-gray-600">Shots</div>
                    <div className="mt-1 space-y-1 text-xs text-gray-700">
                      {(sceneShots ?? []).length === 0 && <div className="text-gray-400">No shots</div>}
                      {(sceneShots ?? []).slice(0, 5).map((shot) => (
                        <div key={shot.id} className="rounded bg-white px-2 py-1 shadow-sm">
                          <span className="font-medium">Shot {shot.shot_number}</span>{" "}
                          <span className="text-gray-600">{shot.shot_type || "Unlabeled"}</span>
                        </div>
                      ))}
                      {(sceneShots ?? []).length > 5 && (
                        <div className="text-[11px] text-gray-500">Showing first 5</div>
                      )}
                    </div>
                  </div>
                </div>
                {showStructureEditor && (
                  <div className="mt-4 border-t border-gray-100 pt-3">
                    <SceneStructurePanel
                      scriptId={script.id}
                      canEdit={canEditStructure}
                      onStructureLoaded={setStructuredScenes}
                    />
                  </div>
                )}
              </>
            ) : (
              <p className="mt-3 text-xs text-gray-500">No matching structured scene found.</p>
            )}
          </div>
        </div>
      </div>
    </Section>
  );
}

function Section({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
        {description && <p className="text-sm text-gray-500">{description}</p>}
      </div>
      <div className="rounded-xl bg-white shadow">{children}</div>
    </section>
  );
}

function SceneDetails({
  scene,
  dialogues,
  directions,
}: {
  scene: ScriptScene | null;
  dialogues: ScriptDialogue[];
  directions: ScriptDirection[];
}) {
  if (!scene) {
    return <p className="p-4 text-sm text-gray-500">Select a scene on the left to view details.</p>;
  }
  const sceneNumber = toSceneNumber(scene.scene_number);
  const sceneDialogues = dialogues.filter((item) => {
    if (typeof item === "string") return true;
    const sn = toSceneNumber(item.scene_number);
    return sceneNumber === sn;
  });
  const sceneDirections = directions.filter((item) => {
    if (typeof item === "string") return true;
    const sn = toSceneNumber(item.scene_number);
    return sceneNumber === sn;
  });
  const characters = scene.characters
    ? Array.isArray(scene.characters)
      ? scene.characters.join(", ")
      : String(scene.characters)
    : undefined;

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
        <div className="flex flex-wrap items-center gap-2 text-sm text-gray-600">
          <SceneTag label={`Scene ${sceneNumber ?? "—"}`} />
          {scene.location && <SceneTag label={`Location: ${scene.location}`} />}
          {scene.time && <SceneTag label={`Time: ${scene.time}`} />}
          {characters && <SceneTag label={`Characters: ${characters}`} />}
        </div>
        <p className="mt-3 text-sm text-gray-700">{formatText(scene.description)}</p>
        {scene.notes && (
          <p className="mt-2 text-xs text-gray-500">Notes: {formatText(scene.notes, "—", 200)}</p>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-lg border border-gray-100 bg-white p-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">Dialogue Excerpt</h3>
          <div className="mt-2 space-y-2 text-sm text-gray-600">
            {sceneDialogues.length === 0 && <p className="text-xs text-gray-400">No dialogues</p>}
            {sceneDialogues.slice(0, 6).map((dialogue, idx) => (
              <div key={`dialogue-${sceneNumber}-${idx}`} className="rounded bg-gray-50 p-2 text-xs">
                {typeof dialogue === "string" ? (
                  dialogue
                ) : (
                  <>
                    <span className="font-medium text-gray-700">{dialogue.character || "Character"}:</span>
                    <span>{formatText(dialogue.content, "No lines", 160)}</span>
                    {dialogue.emotion && (
                      <span className="ml-2 text-[11px] text-gray-400">Emotion: {dialogue.emotion}</span>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-gray-100 bg-white p-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">Stage Directions</h3>
          <div className="mt-2 space-y-2 text-sm text-gray-600">
            {sceneDirections.length === 0 && <p className="text-xs text-gray-400">No stage directions</p>}
            {sceneDirections.slice(0, 6).map((direction, idx) => (
              <div key={`direction-${sceneNumber}-${idx}`} className="rounded bg-gray-50 p-2 text-xs">
                {typeof direction === "string" ? (
                  direction
                ) : (
                  <>
                    {direction.type && <SceneTag label={direction.type} />}
                    <span className="ml-1">{formatText(direction.content, "No content", 160)}</span>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
