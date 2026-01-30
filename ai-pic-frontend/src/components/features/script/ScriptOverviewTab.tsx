"use client";

import type { Script } from "@/utils/api";
import type {
  ScriptScene,
  ScriptDialogue,
  ScriptDirection,
} from "@/hooks/useScriptDetail";
import { toSceneNumber } from "@/hooks/useScriptDetail";
import { formatText } from "@/components/features/StoryboardFrameCard";

interface ScriptOverviewTabProps {
  script: Script;
  scenes: ScriptScene[];
  dialogues: ScriptDialogue[];
  directions: ScriptDirection[];
}

export function ScriptOverviewTab({
  script,
  scenes,
  dialogues,
  directions,
}: ScriptOverviewTabProps) {
  return (
    <Section title="剧本概览" description="剧本内容与核心要素速览">
      <div className="grid grid-cols-1 gap-6 p-6 lg:grid-cols-2">
        <div>
          <h3 className="text-sm font-semibold text-gray-700">剧本文本节选</h3>
          <div className="mt-2 max-h-72 overflow-auto rounded-lg border border-gray-100 bg-gray-50 p-4 text-sm leading-6 text-gray-700">
            {(script.content || "暂无内容")
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
            <h3 className="text-sm font-semibold text-gray-700">
              场景摘要（{scenes.length}）
            </h3>
            <div className="mt-2 max-h-60 space-y-2 overflow-auto">
              {scenes.length === 0 && (
                <p className="text-sm text-gray-500">暂无结构化场景</p>
              )}
              {scenes.slice(0, 6).map((scene, idx) => (
                <div
                  key={idx}
                  className="rounded-lg border border-gray-100 bg-gray-50 p-3 text-sm text-gray-700"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">
                      场景 {toSceneNumber(scene.scene_number) ?? idx + 1}
                    </span>
                    {scene.location && (
                      <span className="text-xs text-gray-500">
                        {scene.location}
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-xs text-gray-500">
                    {formatText(scene.description, "暂无描述", 140)}
                  </p>
                </div>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg border border-gray-100 bg-white p-3 shadow-sm">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                对白
              </h4>
              <p className="mt-1 text-lg font-semibold text-gray-900">
                {dialogues.length}
              </p>
              {dialogues.slice(0, 2).map((dialogue, idx) => (
                <p key={idx} className="mt-1 text-xs text-gray-500">
                  {typeof dialogue === "string"
                    ? dialogue
                    : formatText(dialogue.content, "暂无台词", 80)}
                </p>
              ))}
            </div>
            <div className="rounded-lg border border-gray-100 bg-white p-3 shadow-sm">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                舞台指令
              </h4>
              <p className="mt-1 text-lg font-semibold text-gray-900">
                {directions.length}
              </p>
              {directions.slice(0, 2).map((direction, idx) => (
                <p key={idx} className="mt-1 text-xs text-gray-500">
                  {typeof direction === "string"
                    ? direction
                    : formatText(direction.content, "暂无内容", 80)}
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
