"use client";

import { useState } from "react";
import {
  OperatorState,
  StatusPill,
  operatorButtonClass,
} from "@/components/shared";
import { narrativeMemoryAPI } from "@/utils/api/endpoints";
import type { CharacterMemory } from "@/utils/api/types";

export function SharedMemoryList({
  items,
  virtualIpId,
  onChanged,
  setMessage,
}: {
  items: CharacterMemory[];
  virtualIpId: string;
  onChanged: () => Promise<void>;
  setMessage: (value: string) => void;
}) {
  if (!items.length)
    return (
      <OperatorState
        title="尚无已审批公共记忆"
        detail="从 Story 私有记忆提交提升候选后，在此人工批准。"
      />
    );
  return (
    <div className="divide-y divide-gray-100">
      {items.map((item) => (
        <SharedMemory
          key={item.business_id}
          item={item}
          virtualIpId={virtualIpId}
          onChanged={onChanged}
          setMessage={setMessage}
        />
      ))}
    </div>
  );
}

function SharedMemory({
  item,
  virtualIpId,
  onChanged,
  setMessage,
}: {
  item: CharacterMemory;
  virtualIpId: string;
  onChanged: () => Promise<void>;
  setMessage: (value: string) => void;
}) {
  const [content, setContent] = useState(item.content);
  const [busy, setBusy] = useState(false);
  const run = async (mode: "clone" | "supersede") => {
    setBusy(true);
    const response =
      mode === "clone"
        ? await narrativeMemoryAPI.cloneSharedMemory(
            virtualIpId,
            item.business_id,
            content,
          )
        : await narrativeMemoryAPI.supersedeSharedMemory(
            virtualIpId,
            item.business_id,
            item.version,
            content,
          );
    setMessage(
      response.success
        ? `${
            mode === "clone" ? "克隆" : "替代"
          }版本已创建；只影响之后创建或手动同步的 Story`
        : response.error || "公共记忆操作失败",
    );
    if (response.success) await onChanged();
    setBusy(false);
  };
  return (
    <article className="space-y-3 p-5">
      <div className="flex justify-between gap-3">
        <StatusPill tone={item.status === "approved" ? "green" : "gray"}>
          {item.status} · v{item.version}
        </StatusPill>
        {item.supersedes_business_id ? (
          <span className="text-xs text-gray-500">
            替代 {item.supersedes_business_id.slice(0, 8)}
          </span>
        ) : null}
      </div>
      <textarea
        value={content}
        onChange={(event) => setContent(event.target.value)}
        rows={4}
        className="w-full rounded-md border border-gray-300 p-3 text-sm"
      />
      <div className="flex gap-2">
        <button
          type="button"
          disabled={busy || !content.trim()}
          onClick={() => void run("clone")}
          className={operatorButtonClass("secondary")}
        >
          克隆为新版本
        </button>
        <button
          type="button"
          disabled={
            busy || item.status !== "approved" || content === item.content
          }
          onClick={() => void run("supersede")}
          className={operatorButtonClass("primary")}
        >
          保存并 supersede
        </button>
      </div>
      <p className="text-xs text-gray-500">
        不会自动修改在制 Story；其冻结基线保持原版本。
      </p>
    </article>
  );
}
