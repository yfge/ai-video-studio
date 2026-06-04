"use client";

import { useEffect, useState } from "react";
import { operatorButtonClass } from "@/components/shared";
import { timelineAPI } from "@/utils/api/endpoints";
import type { TimelineResponse } from "@/utils/api/types";
import type { StoryboardSupportFrame } from "./WorkspaceStoryboardSupportModel";
import {
  buildShotPlanPromptLayerPatch,
  emptyShotPlanPromptLayers,
  motionTimelineLabel,
  type ShotPlanMotionPoint,
  type ShotPlanPromptLayers,
} from "./WorkspaceStoryboardPromptLayers";

type ShowAlert = (options: {
  message: string;
  variant: "info" | "success" | "warning" | "error";
}) => void;

type LayerTextKey = Exclude<
  keyof ShotPlanPromptLayers,
  "motionTimeline" | "promptMethod"
>;

const LAYER_TEXT_FIELDS: Array<{ key: LayerTextKey; label: string }> = [
  { key: "directionAnchor", label: "方向锚点" },
  { key: "aestheticReference", label: "风格参照" },
  { key: "shotType", label: "景别" },
  { key: "cameraMovement", label: "运镜" },
  { key: "compositionGeometry", label: "几何构图" },
  { key: "emotionalLanding", label: "情绪落点" },
];

export function PromptLayerSummary({
  layers,
}: {
  layers: ShotPlanPromptLayers | null;
}) {
  if (!layers) return null;
  const motion = motionTimelineLabel(layers);
  return (
    <div className="mt-3 rounded-md border border-gray-200 bg-gray-50 p-3 text-[11px] text-gray-600">
      <div className="font-semibold text-gray-900">五层提示词</div>
      <div className="mt-2 grid gap-1 sm:grid-cols-2">
        <PromptLayerValue label="方向" value={layers.directionAnchor} />
        <PromptLayerValue label="参照" value={layers.aestheticReference} />
        <PromptLayerValue label="构图" value={layers.compositionGeometry} />
        <PromptLayerValue label="情绪" value={layers.emotionalLanding} />
      </div>
      {motion ? <div className="mt-2 text-gray-700">{motion}</div> : null}
    </div>
  );
}

export function PromptLayerEditor({
  frame,
  selectedTimelineSpec,
  showAlert,
  onTimelineUpdated,
}: {
  frame: StoryboardSupportFrame;
  selectedTimelineSpec?: TimelineResponse | null;
  showAlert?: ShowAlert;
  onTimelineUpdated?: (timeline: TimelineResponse) => void;
}) {
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [draft, setDraft] = useState<ShotPlanPromptLayers>(
    frame.promptLayers ?? emptyShotPlanPromptLayers(),
  );

  useEffect(() => {
    setDraft(frame.promptLayers ?? emptyShotPlanPromptLayers());
  }, [frame.promptLayers]);

  const canSave = Boolean(selectedTimelineSpec && frame.clipId && !saving);
  const handleSave = async () => {
    if (!selectedTimelineSpec || !frame.clipId) return;
    const patchedSpec = buildShotPlanPromptLayerPatch(
      selectedTimelineSpec,
      frame.clipId,
      draft,
    );
    if (!patchedSpec) {
      showAlert?.({ message: "未找到可编辑的时间轴片段", variant: "warning" });
      return;
    }

    setSaving(true);
    try {
      const response = await timelineAPI.updateTimeline(selectedTimelineSpec.id, {
        expected_version: selectedTimelineSpec.version,
        spec: patchedSpec,
      });
      if (!response.success || !response.data) {
        showAlert?.({
          message: response.error || "五层提示词保存失败",
          variant: "error",
        });
        return;
      }
      onTimelineUpdated?.(response.data);
      showAlert?.({ message: "五层提示词已保存", variant: "success" });
      setOpen(false);
    } catch (error) {
      showAlert?.({
        message:
          error instanceof Error
            ? `五层提示词保存失败：${error.message}`
            : "五层提示词保存失败",
        variant: "error",
      });
    } finally {
      setSaving(false);
    }
  };

  if (!selectedTimelineSpec || !frame.clipId) return null;

  return (
    <div className="mt-3">
      <button
        type="button"
        className={operatorButtonClass("secondary")}
        onClick={() => setOpen((value) => !value)}
      >
        {open ? "收起五层编辑" : "编辑五层提示词"}
      </button>
      {open ? (
        <div className="mt-3 grid gap-2 rounded-md border border-gray-200 bg-white p-3">
          {LAYER_TEXT_FIELDS.slice(0, 5).map((field) => (
            <LayerTextArea
              key={field.key}
              label={field.label}
              value={draft[field.key]}
              onChange={(value) =>
                setDraft((prev) => ({ ...prev, [field.key]: value }))
              }
            />
          ))}
          <MotionTimelineEditor
            points={draft.motionTimeline}
            onChange={(motionTimeline) =>
              setDraft((prev) => ({ ...prev, motionTimeline }))
            }
          />
          {LAYER_TEXT_FIELDS.slice(5).map((field) => (
            <LayerTextArea
              key={field.key}
              label={field.label}
              value={draft[field.key]}
              onChange={(value) =>
                setDraft((prev) => ({ ...prev, [field.key]: value }))
              }
            />
          ))}
          <button
            type="button"
            disabled={!canSave}
            className={operatorButtonClass("primary")}
            onClick={handleSave}
          >
            {saving ? "保存中..." : "保存五层提示词"}
          </button>
        </div>
      ) : null}
    </div>
  );
}

function PromptLayerValue({ label, value }: { label: string; value: string }) {
  if (!value) return null;
  return (
    <div>
      <span className="text-gray-500">{label}：</span>
      <span className="text-gray-800">{value}</span>
    </div>
  );
}

function LayerTextArea({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid gap-1 text-[11px] font-medium text-gray-700">
      {label}
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="min-h-14 rounded-md border border-gray-200 p-2 text-xs font-normal text-gray-800"
      />
    </label>
  );
}

function MotionTimelineEditor({
  points,
  onChange,
}: {
  points: ShotPlanMotionPoint[];
  onChange: (points: ShotPlanMotionPoint[]) => void;
}) {
  const rows = points.length ? points : emptyShotPlanPromptLayers().motionTimeline;
  return (
    <div className="grid gap-1 text-[11px] font-medium text-gray-700">
      秒级动作轴
      <div className="grid gap-2">
        {rows.map((point, index) => (
          <div key={index} className="grid grid-cols-[84px_minmax(0,1fr)] gap-2">
            <input
              type="number"
              value={point.atMs}
              min={0}
              onChange={(event) =>
                onChange(
                  rows.map((item, itemIndex) =>
                    itemIndex === index
                      ? { ...item, atMs: Number(event.target.value) }
                      : item,
                  ),
                )
              }
              className="rounded-md border border-gray-200 px-2 text-xs font-normal text-gray-800"
            />
            <input
              value={point.action}
              onChange={(event) =>
                onChange(
                  rows.map((item, itemIndex) =>
                    itemIndex === index
                      ? { ...item, action: event.target.value }
                      : item,
                  ),
                )
              }
              className="rounded-md border border-gray-200 px-2 text-xs font-normal text-gray-800"
            />
          </div>
        ))}
      </div>
    </div>
  );
}
