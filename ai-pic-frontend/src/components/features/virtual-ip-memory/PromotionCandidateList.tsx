"use client";

import { useState } from "react";
import {
  OperatorState,
  StatusPill,
  operatorButtonClass,
} from "@/components/shared";
import { narrativeMemoryAPI } from "@/utils/api/endpoints";
import type { CharacterMemory, MemoryPromotion } from "@/utils/api/types";

export function PromotionCandidateList({
  items,
  shared,
  onChanged,
  setMessage,
}: {
  items: MemoryPromotion[];
  shared: CharacterMemory[];
  onChanged: () => Promise<void>;
  setMessage: (value: string) => void;
}) {
  if (!items.length) return <OperatorState title="没有公共记忆提升候选" />;
  return (
    <div className="divide-y divide-gray-100">
      {items.map((item) => (
        <PromotionCandidate
          key={item.business_id}
          item={item}
          hasExactMatch={shared.some(
            (memory) => memory.content === item.candidate_content,
          )}
          onChanged={onChanged}
          setMessage={setMessage}
        />
      ))}
    </div>
  );
}

function PromotionCandidate({
  item,
  hasExactMatch,
  onChanged,
  setMessage,
}: {
  item: MemoryPromotion;
  hasExactMatch: boolean;
  onChanged: () => Promise<void>;
  setMessage: (value: string) => void;
}) {
  const [content, setContent] = useState(item.candidate_content);
  const [reason, setReason] = useState(item.decision_reason || "");
  const [busy, setBusy] = useState(false);
  const save = async () => {
    setBusy(true);
    const response = await narrativeMemoryAPI.updatePromotion(
      item.business_id,
      {
        expected_version: item.version,
        candidate_content: content,
        decision_reason: reason || undefined,
      },
    );
    setMessage(
      response.success
        ? "公共记忆候选已人工编辑（未调用模型）"
        : response.error || "保存失败",
    );
    if (response.success) await onChanged();
    setBusy(false);
  };
  const review = async (action: "approve" | "reject") => {
    setBusy(true);
    const response = await narrativeMemoryAPI.reviewPromotion(
      item.business_id,
      action,
      item.version,
      reason || undefined,
    );
    setMessage(
      response.success
        ? action === "approve"
          ? "公共记忆已人工批准"
          : "候选已拒绝"
        : response.error || "审核失败",
    );
    if (response.success) await onChanged();
    setBusy(false);
  };
  return (
    <article className="space-y-3 p-5">
      <div className="flex justify-between gap-3">
        <div className="flex gap-2">
          <StatusPill
            tone={
              item.status === "approved"
                ? "green"
                : item.status === "rejected"
                ? "gray"
                : "amber"
            }
          >
            {item.status}
          </StatusPill>
          <StatusPill tone={hasExactMatch ? "amber" : "blue"}>
            {hasExactMatch ? "与现有记忆相同" : "新增或有差异"}
          </StatusPill>
        </div>
        <span className="text-xs text-gray-500">v{item.version}</span>
      </div>
      <p className="text-xs text-gray-500">
        来源 Story {item.source_story_business_id.slice(0, 8)} ·{" "}
        {item.source_memory_ids.length} 条私有记忆
      </p>
      <textarea
        value={content}
        disabled={item.status !== "pending"}
        onChange={(event) => setContent(event.target.value)}
        rows={4}
        className="w-full rounded-md border border-gray-300 p-3 text-sm disabled:bg-gray-50"
      />
      <input
        value={reason}
        disabled={item.status !== "pending"}
        onChange={(event) => setReason(event.target.value)}
        placeholder="审核/编辑理由（可选）"
        className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm disabled:bg-gray-50"
      />
      {item.status === "pending" ? (
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={busy || !content.trim()}
            onClick={() => void save()}
            className={operatorButtonClass("secondary")}
          >
            保存编辑
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => void review("approve")}
            className={operatorButtonClass("primary")}
          >
            人工批准
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => void review("reject")}
            className={operatorButtonClass("danger")}
          >
            拒绝
          </button>
        </div>
      ) : null}
    </article>
  );
}
