"use client";

import { useEffect, useState } from "react";
import {
  OperatorPanel,
  OperatorSectionHeader,
  StatusPill,
  operatorButtonClass,
} from "@/components/shared";
import type {
  AdaptationPlanEpisode,
  StoryNovelRevision,
} from "@/utils/api/types";
import { StoryNovelAdaptationEpisodeCard } from "./StoryNovelAdaptationEpisodeCard";
import {
  adaptationEvidenceReady,
  adaptationGateMessage,
} from "./storyNovelAdaptationGate";

interface Props {
  revision: StoryNovelRevision;
  busy: boolean;
  onGenerate: () => void;
  onSave: (version: number, rows: AdaptationPlanEpisode[]) => void;
  onApprove: (version: number) => void;
  onApply: () => void;
}

export function StoryNovelAdaptationPanel({
  revision,
  busy,
  onGenerate,
  onSave,
  onApprove,
  onApply,
}: Props) {
  const plan = revision.adaptation_plan;
  const editable = revision.adaptation_plan_status === "draft";
  const novelApproved = revision.lifecycle_status === "approved";
  const planCanGenerate =
    novelApproved &&
    ["empty", "stale"].includes(revision.adaptation_plan_status);
  const episodesCanApply =
    novelApproved &&
    ["approved", "applied"].includes(revision.adaptation_plan_status) &&
    adaptationEvidenceReady(revision);
  const [rows, setRows] = useState<AdaptationPlanEpisode[]>(
    plan?.episodes || [],
  );
  useEffect(() => setRows(plan?.episodes || []), [plan]);
  const update = (index: number, patch: Partial<AdaptationPlanEpisode>) =>
    setRows((items) =>
      items.map((item, rowIndex) =>
        rowIndex === index ? { ...item, ...patch } : item,
      ),
    );
  const addEpisode = () => {
    const firstChapter = revision.chapters[0]?.business_id || "";
    setRows((items) => [
      ...items,
      {
        episode_number: items.length + 1,
        title: `第${items.length + 1}集`,
        source_chapter_business_ids: firstChapter ? [firstChapter] : [],
        adaptation_goal: "",
        summary: "",
        plot_points: [],
        conflicts: [],
        character_arcs: {},
        cliffhanger: "",
      },
    ]);
  };
  return (
    <OperatorPanel id="novel-adaptation" className="scroll-mt-24">
      <OperatorSectionHeader
        title="4. 小说改编计划 → 剧集"
        subtitle="确认来源章节、改编目标、情节点、冲突、角色弧和卡点后再创建 Episode"
        action={
          <StatusPill
            tone={
              revision.adaptation_plan_status === "approved" ||
              revision.adaptation_plan_status === "applied"
                ? "green"
                : "amber"
            }
          >
            {revision.adaptation_plan_status}
          </StatusPill>
        }
      />
      <div
        aria-label="权威生产链路"
        className="border-b border-gray-100 px-5 py-3 text-xs font-medium text-gray-700"
      >
        故事大纲 → 小说审批 → 改编计划 → 剧集 → 剧本
      </div>
      <p
        role="status"
        className={`px-5 pt-4 text-xs ${
          episodesCanApply ? "text-green-700" : "text-amber-700"
        }`}
      >
        {adaptationGateMessage(revision)}
      </p>
      {!plan ? (
        <div className="flex flex-wrap gap-2 p-5">
          <button
            type="button"
            disabled={busy || !planCanGenerate}
            onClick={onGenerate}
            className={operatorButtonClass("primary")}
          >
            生成分集改编计划
          </button>
          <button
            type="button"
            disabled
            className={operatorButtonClass("secondary")}
          >
            创建剧集
          </button>
        </div>
      ) : (
        <div className="space-y-4 p-5">
          {rows.map((row, index) => (
            <StoryNovelAdaptationEpisodeCard
              key={`${row.episode_number}-${index}`}
              row={row}
              index={index}
              busy={busy}
              editable={editable}
              canRemove={rows.length > 1}
              onChange={(patch) => update(index, patch)}
              onRemove={() =>
                setRows((items) =>
                  items
                    .filter((_, rowIndex) => rowIndex !== index)
                    .map((item, rowIndex) => ({
                      ...item,
                      episode_number: rowIndex + 1,
                    })),
                )
              }
            />
          ))}
          <div className="flex flex-wrap gap-2">
            {revision.adaptation_plan_status === "stale" ? (
              <button
                type="button"
                disabled={busy || !planCanGenerate}
                onClick={onGenerate}
                className={operatorButtonClass("primary")}
              >
                重新生成分集改编计划
              </button>
            ) : null}
            <button
              type="button"
              disabled={busy || !editable}
              onClick={addEpisode}
              className={operatorButtonClass("secondary")}
            >
              增加一集
            </button>
            <button
              type="button"
              disabled={busy || !editable || !rows.length}
              onClick={() =>
                onSave(
                  plan.version,
                  rows.map((row, index) => ({
                    ...row,
                    episode_number: index + 1,
                  })),
                )
              }
              className={operatorButtonClass("primary")}
            >
              保存计划
            </button>
            {revision.adaptation_plan_status === "draft" ? (
              <button
                type="button"
                disabled={busy}
                onClick={() => onApprove(plan.version)}
                className={operatorButtonClass("secondary")}
              >
                审批计划
              </button>
            ) : null}
            <button
              type="button"
              disabled={busy || !episodesCanApply}
              onClick={onApply}
              className={operatorButtonClass("primary")}
            >
              {revision.adaptation_plan_status === "applied"
                ? "返回既有剧集"
                : "创建剧集"}
            </button>
          </div>
        </div>
      )}
    </OperatorPanel>
  );
}
