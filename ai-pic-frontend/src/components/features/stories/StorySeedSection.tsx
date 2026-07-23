"use client";

import { useEffect, useMemo, useState } from "react";
import {
  OperatorPanel,
  OperatorSectionHeader,
  StatusPill,
  operatorButtonClass,
} from "@/components/shared";
import { storyAPI } from "@/utils/api/endpoints";
import type { Story } from "@/utils/api/types";
import {
  resolveStorySeed,
  StorySeedEditor,
  StorySeedView,
} from "./StorySeedFields";

export function StorySeedSection({ story }: { story: Story }) {
  const initial = useMemo(() => resolveStorySeed(story), [story]);
  const [seed, setSeed] = useState(initial);
  const [status, setStatus] = useState(story.story_seed_status || "draft");
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");
  useEffect(() => {
    setSeed(initial);
    setStatus(story.story_seed_status || "draft");
  }, [initial, story.story_seed_status]);

  const save = async (status: "draft" | "confirmed") => {
    try {
      setSaving(true);
      const response = await storyAPI.updateStory(story.business_id, {
        story_seed: seed,
        story_seed_status: status,
      });
      if (!response.success || !response.data) throw new Error(response.error);
      setSeed(response.data.story_seed || seed);
      setStatus(response.data.story_seed_status || status);
      setEditing(false);
      setNotice(
        status === "confirmed"
          ? "Story Seed 已确认；不会自动生成小说或分集"
          : "Story Seed 已本地保存；未调用模型",
      );
    } catch (error) {
      setNotice(`保存失败：${String(error)}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <OperatorPanel>
      <OperatorSectionHeader
        title="1. 故事大纲（Story Seed）"
        subtitle="轻量初始条件；商业节奏、可拍性和连续性在下游检查"
        action={
          <div className="flex items-center gap-2">
            <StatusPill tone={status === "confirmed" ? "green" : "gray"}>
              {status === "confirmed" ? "已确认" : "草稿"}
            </StatusPill>
            <button
              type="button"
              onClick={() => setEditing((value) => !value)}
              className={operatorButtonClass("secondary")}
            >
              {editing ? "取消编辑" : "编辑大纲"}
            </button>
          </div>
        }
      />
      <div className="space-y-5 p-5">
        <BaselineEvidence story={story} />
        {notice ? (
          <p className="text-xs text-gray-600" role="status">
            {notice}
          </p>
        ) : null}
        {editing ? (
          <StorySeedEditor seed={seed} onChange={setSeed} />
        ) : (
          <StorySeedView seed={seed} />
        )}
        {editing ? (
          <div className="flex flex-wrap justify-end gap-2 border-t border-gray-100 pt-4">
            <span className="mr-auto text-xs text-gray-500">
              保存与确认均不调用模型；修改会将小说和下游标记为待复核。
            </span>
            <button
              type="button"
              disabled={saving}
              onClick={() => void save("draft")}
              className={operatorButtonClass("secondary")}
            >
              保存大纲
            </button>
            <button
              type="button"
              disabled={saving}
              onClick={() => void save("confirmed")}
              className={operatorButtonClass("primary")}
            >
              确认 Story Seed
            </button>
          </div>
        ) : null}
      </div>
    </OperatorPanel>
  );
}

function BaselineEvidence({ story }: { story: Story }) {
  const downstream = story.extra_metadata?.story_seed_downstream as
    | { status?: string }
    | undefined;
  return (
    <div className="flex flex-wrap gap-2 text-xs">
      <StatusPill tone="blue">
        公共记忆基线 v{story.shared_memory_baseline_version || 0}
      </StatusPill>
      <StatusPill tone="gray">Seed v{story.story_seed_version || 1}</StatusPill>
      {downstream?.status === "review_required" ? (
        <StatusPill tone="amber">下游待复核</StatusPill>
      ) : null}
    </div>
  );
}
