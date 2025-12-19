"use client";

import type { Script } from "@/utils/api";
import type { ScriptScene, ScriptDialogue, ScriptDirection } from "@/hooks/useScriptDetail";
import { toSceneNumber } from "@/hooks/useScriptDetail";
import { formatText } from "@/components/features/StoryboardFrameCard";

interface ScriptOverviewTabProps {
  script: Script;
  scenes: ScriptScene[];
  dialogues: ScriptDialogue[];
  directions: ScriptDirection[];
}

export function ScriptOverviewTab({ script, scenes, dialogues, directions }: ScriptOverviewTabProps) {
  return (
    <Section title="Script Overview" description="Quick overview of script content and core elements">
      <div className="grid grid-cols-1 gap-6 p-6 lg:grid-cols-2">
        <div>
          <h3 className="text-sm font-semibold text-gray-700">Script Text Excerpt</h3>
          <div className="mt-2 max-h-72 overflow-auto rounded-lg border border-gray-100 bg-gray-50 p-4 text-sm leading-6 text-gray-700">
            {(script.content || "No content")
              .split("\n")
              .slice(0, 120)
              .map((line, idx) => (
                <p key={idx} className="whitespace-pre-wrap">
                  {line}
                </p>
              ))}
          </div>
        </div>
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-700">Scene Summary ({scenes.length})</h3>
            <div className="mt-2 max-h-60 space-y-2 overflow-auto">
              {scenes.length === 0 && <p className="text-sm text-gray-500">No structured scenes</p>}
              {scenes.slice(0, 6).map((scene, idx) => (
                <div
                  key={idx}
                  className="rounded-lg border border-gray-100 bg-gray-50 p-3 text-sm text-gray-700"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">Scene {toSceneNumber(scene.scene_number) ?? idx + 1}</span>
                    {scene.location && <span className="text-xs text-gray-500">{scene.location}</span>}
                  </div>
                  <p className="mt-1 text-xs text-gray-500">
                    {formatText(scene.description, "No description", 140)}
                  </p>
                </div>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg border border-gray-100 bg-white p-3 shadow-sm">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500">Dialogues</h4>
              <p className="mt-1 text-lg font-semibold text-gray-900">{dialogues.length}</p>
              {dialogues.slice(0, 2).map((dialogue, idx) => (
                <p key={idx} className="mt-1 text-xs text-gray-500">
                  {typeof dialogue === "string"
                    ? dialogue
                    : formatText(dialogue.content, "No lines", 80)}
                </p>
              ))}
            </div>
            <div className="rounded-lg border border-gray-100 bg-white p-3 shadow-sm">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                Stage Directions
              </h4>
              <p className="mt-1 text-lg font-semibold text-gray-900">{directions.length}</p>
              {directions.slice(0, 2).map((direction, idx) => (
                <p key={idx} className="mt-1 text-xs text-gray-500">
                  {typeof direction === "string"
                    ? direction
                    : formatText(direction.content, "No content", 80)}
                </p>
              ))}
            </div>
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
