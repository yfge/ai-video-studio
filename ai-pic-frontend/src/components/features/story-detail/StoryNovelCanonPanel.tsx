"use client";

import { useEffect, useRef, useState } from "react";
import {
  OperatorPanel,
  StatusPill,
  operatorButtonClass,
} from "@/components/shared";
import type {
  StoryNovelCanon,
  StoryNovelRepairGroup,
  StoryNovelRevision,
} from "@/utils/api/types";

export function StoryNovelCanonPanel({
  revision,
  busy,
  onSave,
}: {
  revision: StoryNovelRevision;
  busy: boolean;
  onSave: (canon: StoryNovelCanon) => Promise<boolean>;
}) {
  const canon = revision.generation_plan?.canon;
  const canonText = canon ? JSON.stringify(canon, null, 2) : "";
  const canonVersion = `${revision.business_id}:${
    revision.generation_plan?.canon_hash || ""
  }`;
  const previousCanonVersion = useRef(canonVersion);
  const [draft, setDraft] = useState(canonText);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (previousCanonVersion.current === canonVersion) return;
    previousCanonVersion.current = canonVersion;
    setDraft(canonText);
    setError(null);
  }, [canonText, canonVersion]);
  if (!canon) return null;
  const repairs = revision.continuity_report?.repair_groups || [];

  const applySuggestion = (group: StoryNovelRepairGroup) => {
    try {
      const current = JSON.parse(draft) as StoryNovelCanon;
      setDraft(JSON.stringify(applyCanonSuggestion(current, group), null, 2));
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "修复建议无法应用");
    }
  };
  const save = async () => {
    try {
      const parsed = JSON.parse(draft) as StoryNovelCanon;
      setError(null);
      if (!(await onSave(parsed))) setError("Canon 保存失败");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Canon JSON 无效");
    }
  };

  return (
    <OperatorPanel>
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 p-5">
        <div>
          <h3 className="text-sm font-semibold">修订版 Canon</h3>
          <p className="mt-1 text-xs text-gray-500">
            保存只更新结构化事实，不调用模型；变更会从最早引用章节开始失效。
          </p>
        </div>
        <StatusPill tone="blue">
          {revision.generation_plan?.canon_hash?.slice(0, 10)}
        </StatusPill>
      </div>
      {repairs.length ? (
        <div className="border-b border-gray-100 p-5">
          <h4 className="text-xs font-semibold">待人工确认的修复建议</h4>
          <div className="mt-3 grid gap-2">
            {repairs.map((group) => (
              <div
                key={group.id}
                className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs"
              >
                <p className="font-medium">{group.title || group.id}</p>
                <p className="mt-1 text-gray-600">
                  建议值：{JSON.stringify(group.suggested_value)}
                </p>
                <button
                  type="button"
                  disabled={busy || !group.canon_target}
                  onClick={() => applySuggestion(group)}
                  className={operatorButtonClass("secondary", "mt-2")}
                >
                  填入 Canon 草稿
                </button>
              </div>
            ))}
          </div>
        </div>
      ) : null}
      <div className="p-5">
        <label className="text-xs font-medium">
          Canon 结构化草稿
          <textarea
            aria-label="Canon 结构化草稿"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            className="mt-2 min-h-80 w-full rounded-md border border-gray-300 p-3 font-mono text-xs"
          />
        </label>
        {revision.continuity_ledger?.stale_from_position ? (
          <p className="mt-2 text-xs text-amber-700">
            当前从第 {revision.continuity_ledger.stale_from_position}{" "}
            章起待重生成。
          </p>
        ) : null}
        {draft !== canonText ? (
          <p className="mt-2 text-xs text-amber-700">Canon 草稿有未保存修改</p>
        ) : null}
        {error ? (
          <p role="alert" className="mt-2 text-xs text-red-600">
            {error}
          </p>
        ) : null}
        <button
          type="button"
          disabled={busy}
          onClick={() => void save()}
          className={operatorButtonClass("primary", "mt-3")}
        >
          人工确认并保存 Canon
        </button>
      </div>
    </OperatorPanel>
  );
}

export function applyCanonSuggestion(
  canon: StoryNovelCanon,
  group: StoryNovelRepairGroup,
): StoryNovelCanon {
  const target = group.canon_target;
  if (!target?.field) throw new Error("修复建议缺少 Canon 字段");
  const result = JSON.parse(JSON.stringify(canon)) as StoryNovelCanon;
  if (target.section === "initial_state") {
    const subject = result.initial_state[target.item_id || ""];
    if (!subject) throw new Error("修复建议引用未知 Canon 实体");
    setPath(subject, target.field, group.suggested_value);
    return result;
  }
  const rows = result[target.section] as Array<Record<string, unknown>>;
  const item = rows.find(
    (row) => row.id === target.item_id || row.character_id === target.item_id,
  );
  if (!item) throw new Error("修复建议引用未知 Canon 项");
  setPath(item, target.field, group.suggested_value);
  return result;
}

function setPath(
  target: Record<string, unknown>,
  path: string,
  value: unknown,
) {
  const parts = path.split(".");
  let current = target;
  for (const part of parts.slice(0, -1)) {
    const next = current[part];
    current =
      next && typeof next === "object"
        ? (next as Record<string, unknown>)
        : ((current[part] = {}) as Record<string, unknown>);
  }
  current[parts.at(-1)!] = value;
}
