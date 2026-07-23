"use client";

import { useEffect, useState } from "react";
import {
  OperatorInspector,
  StatusPill,
  operatorButtonClass,
} from "@/components/shared";
import type { NarrativeAnchor } from "@/utils/api/types";
import type { MemoryWorkspaceItem } from "@/hooks/useStoryMemoryWorkspace";

export function StoryMemoryInspector(props: {
  item: MemoryWorkspaceItem | null;
  anchors: NarrativeAnchor[];
  onSave: (item: MemoryWorkspaceItem, text: string) => Promise<void>;
  onReview: (
    item: MemoryWorkspaceItem,
    action: "approve" | "reject",
  ) => Promise<void>;
  onSplit: (item: MemoryWorkspaceItem, contents: string[]) => Promise<void>;
  onMerge: (
    item: MemoryWorkspaceItem,
    targetBusinessId: string,
    mergedContent?: string,
  ) => Promise<void>;
  onPromote: (
    item: MemoryWorkspaceItem,
    candidateContent: string,
  ) => Promise<void>;
}) {
  const { item } = props;
  const [text, setText] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [splitText, setSplitText] = useState("");
  const [mergeId, setMergeId] = useState("");
  useEffect(() => {
    setText(item ? ("event_type" in item ? item.summary : item.content) : "");
    setMessage("");
    setSplitText("");
    setMergeId("");
  }, [item]);
  const run = async (action: () => Promise<void>, success: string) => {
    try {
      setBusy(true);
      await action();
      setMessage(success);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(false);
    }
  };

  return (
    <OperatorInspector title="锚点与审核" subtitle="来源、版本和人工决策">
      {!item ? (
        <p className="text-sm text-gray-500">选择一条事件或记忆查看证据。</p>
      ) : (
        <div className="space-y-5">
          <div className="flex flex-wrap gap-2">
            <StatusPill tone={statusTone(item.status)}>
              {item.status}
            </StatusPill>
            <StatusPill tone="gray">v{item.version}</StatusPill>
            <StatusPill tone="blue">
              {"event_type" in item ? "客观事件" : item.scope}
            </StatusPill>
          </div>
          <label className="block text-xs font-medium text-gray-600">
            候选内容
            <textarea
              value={text}
              disabled={!["candidate", "stale"].includes(item.status)}
              onChange={(event) => setText(event.target.value)}
              rows={7}
              className="mt-2 w-full rounded-md border border-gray-300 p-3 text-sm focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
            />
          </label>
          <AnchorEvidence item={item} anchors={props.anchors} />
          {item.invalidation ? (
            <div className="rounded-md border border-red-200 bg-red-50 p-3 text-xs text-red-800">
              来源已变化：
              {String(item.invalidation.reason_code || "source_changed")}
            </div>
          ) : null}
          {["candidate", "stale"].includes(item.status) ? (
            <div className="grid gap-2">
              <button
                type="button"
                disabled={busy || !text.trim()}
                onClick={() =>
                  void run(() => props.onSave(item, text), "候选已本地保存")
                }
                className={operatorButtonClass("secondary")}
              >
                保存编辑（不调用模型）
              </button>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  disabled={busy}
                  onClick={() =>
                    void run(() => props.onReview(item, "approve"), "已批准")
                  }
                  className={operatorButtonClass("primary")}
                >
                  批准
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() =>
                    void run(() => props.onReview(item, "reject"), "已拒绝")
                  }
                  className={operatorButtonClass("danger")}
                >
                  拒绝
                </button>
              </div>
              <details className="rounded-md border border-gray-200 p-3">
                <summary className="cursor-pointer text-xs font-medium">
                  拆分 / 合并候选
                </summary>
                <label className="mt-3 block text-xs text-gray-600">
                  拆分内容（每行一条，至少两条）
                  <textarea
                    rows={4}
                    value={splitText}
                    onChange={(event) => setSplitText(event.target.value)}
                    className="mt-1 w-full rounded-md border border-gray-300 p-2"
                  />
                </label>
                <button
                  type="button"
                  disabled={
                    busy || splitText.split("\n").filter(Boolean).length < 2
                  }
                  onClick={() =>
                    void run(
                      () =>
                        props.onSplit(
                          item,
                          splitText
                            .split("\n")
                            .map((value) => value.trim())
                            .filter(Boolean),
                        ),
                      "候选已拆分；原候选保留为 superseded",
                    )
                  }
                  className={operatorButtonClass("secondary", "mt-2 w-full")}
                >
                  拆分候选
                </button>
                <label className="mt-3 block text-xs text-gray-600">
                  合并目标 business ID
                  <input
                    value={mergeId}
                    onChange={(event) => setMergeId(event.target.value)}
                    className="mt-1 w-full rounded-md border border-gray-300 p-2"
                  />
                </label>
                <button
                  type="button"
                  disabled={busy || !mergeId.trim()}
                  onClick={() =>
                    void run(
                      () => props.onMerge(item, mergeId.trim()),
                      "候选已合并；原候选保留为 superseded",
                    )
                  }
                  className={operatorButtonClass("secondary", "mt-2 w-full")}
                >
                  合并候选
                </button>
              </details>
            </div>
          ) : null}
          {item.status === "approved" && !("event_type" in item) ? (
            <button
              type="button"
              disabled={busy}
              onClick={() =>
                void run(
                  () => props.onPromote(item, text),
                  "已提交公共记忆提升候选；仍需人工批准",
                )
              }
              className={operatorButtonClass("secondary", "w-full")}
            >
              提交为角色公共记忆候选
            </button>
          ) : null}
          <p className="text-xs text-gray-500" aria-live="polite">
            {message}
          </p>
        </div>
      )}
    </OperatorInspector>
  );
}

function AnchorEvidence({
  item,
  anchors,
}: {
  item: MemoryWorkspaceItem;
  anchors: NarrativeAnchor[];
}) {
  const ids =
    "event_type" in item
      ? [item.occurred_at_anchor_business_id]
      : [
          item.occurred_at_anchor_business_id,
          item.learned_at_anchor_business_id,
          item.effective_from_anchor_business_id,
        ];
  const selected = ids
    .filter(Boolean)
    .map((id) => anchors.find((anchor) => anchor.business_id === id));
  return (
    <div>
      <h3 className="text-xs font-semibold text-gray-700">
        发生 / 获知 / 生效锚点
      </h3>
      <ul className="mt-2 space-y-2 text-xs text-gray-600">
        {selected.map((anchor, index) => (
          <li
            key={`${anchor?.business_id}-${index}`}
            className="rounded bg-gray-50 p-2"
          >
            {anchor
              ? `${anchor.anchor_type} · 序列 ${anchor.narrative_sequence}${
                  anchor.story_time_label ? ` · ${anchor.story_time_label}` : ""
                }`
              : "锚点待确认"}
          </li>
        ))}
      </ul>
    </div>
  );
}

function statusTone(status: string): "green" | "amber" | "red" | "gray" {
  if (status === "approved") return "green";
  if (status === "candidate") return "amber";
  if (status === "stale") return "red";
  return "gray";
}
