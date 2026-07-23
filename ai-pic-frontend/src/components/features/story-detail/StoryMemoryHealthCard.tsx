"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { StatusPill, operatorButtonClass } from "@/components/shared";
import { narrativeMemoryAPI } from "@/utils/api/endpoints";
import type {
  MemorySummary,
  SharedMemoryBaselineDiff,
} from "@/utils/api/types";

export function StoryMemoryHealthCard({ storyId }: { storyId: string }) {
  const [summary, setSummary] = useState<MemorySummary | null>(null);
  const [error, setError] = useState("");
  const [diff, setDiff] = useState<SharedMemoryBaselineDiff | null>(null);
  const [message, setMessage] = useState("");
  useEffect(() => {
    let active = true;
    void narrativeMemoryAPI.getSummary(storyId).then((response) => {
      if (!active) return;
      if (response.success && response.data) setSummary(response.data);
      else setError(response.error || "叙事记忆摘要加载失败");
    });
    return () => {
      active = false;
    };
  }, [storyId]);

  const loadDiff = async () => {
    const response = await narrativeMemoryAPI.getBaselineDiff(storyId);
    if (response.success && response.data) {
      setDiff(response.data);
      setMessage(
        response.data.has_updates
          ? "发现公共记忆更新；默认保持当前版本。"
          : "当前基线已是最新版本。",
      );
    } else {
      setMessage(response.error || "公共记忆差异加载失败");
    }
  };

  const sync = async () => {
    if (!summary || !diff?.has_updates) return;
    if (
      !window.confirm(
        "同步只更新公共记忆基线并标记下游 stale，不会自动重生成。确认继续？",
      )
    ) {
      return;
    }
    const response = await narrativeMemoryAPI.syncBaseline(
      storyId,
      summary.shared_baseline_version,
    );
    if (!response.success) {
      setMessage(response.error || "同步失败；基线可能已被其他窗口更新");
      return;
    }
    setMessage("公共记忆基线已同步；受影响内容已标记 review_required/stale。");
    setDiff(null);
  };

  return (
    <section
      aria-labelledby="memory-health-title"
      className="border-t border-gray-100 pt-4"
    >
      <div className="flex items-center justify-between gap-3">
        <h2 id="memory-health-title" className="text-sm font-semibold">
          叙事记忆健康
        </h2>
        <Link
          href={`/stories/${storyId}/memory`}
          className={operatorButtonClass("secondary")}
        >
          进入叙事记忆
        </Link>
      </div>
      {!summary && !error ? (
        <p className="mt-3 text-xs text-gray-500" role="status">
          正在加载记忆状态…
        </p>
      ) : null}
      {error ? (
        <p className="mt-3 text-xs text-red-700" role="alert">
          {error}
        </p>
      ) : null}
      {summary ? (
        <div className="mt-3 flex flex-wrap gap-2">
          <StatusPill tone="blue">
            私有记忆 {summary.private_memory_count}
          </StatusPill>
          <StatusPill tone={summary.pending_count ? "amber" : "gray"}>
            待审核 {summary.pending_count}
          </StatusPill>
          <StatusPill tone={summary.conflict_count ? "red" : "gray"}>
            冲突 {summary.conflict_count}
          </StatusPill>
          <StatusPill tone={summary.stale_count ? "red" : "gray"}>
            stale {summary.stale_count}
          </StatusPill>
          <StatusPill tone="gray">
            公共基线 v{summary.shared_baseline_version}
          </StatusPill>
          <button
            type="button"
            onClick={() => void loadDiff()}
            className={operatorButtonClass("secondary")}
          >
            查看公共记忆差异
          </button>
        </div>
      ) : null}
      {diff ? (
        <div className="mt-3 rounded-md border border-gray-200 p-3 text-xs">
          <div className="flex flex-wrap gap-2">
            <StatusPill tone={diff.added.length ? "blue" : "gray"}>
              新增 {diff.added.length}
            </StatusPill>
            <StatusPill tone={diff.modified.length ? "amber" : "gray"}>
              修改 {diff.modified.length}
            </StatusPill>
            <StatusPill tone={diff.removed.length ? "red" : "gray"}>
              移除 {diff.removed.length}
            </StatusPill>
          </div>
          <p className="mt-2 text-gray-600">
            当前 v{diff.frozen_version}；可用 v{diff.available_version}。在制
            Story 默认保持当前版本。
          </p>
          {diff.has_updates ? (
            <button
              type="button"
              onClick={() => void sync()}
              className={operatorButtonClass("danger", "mt-3")}
            >
              确认同步并标记下游 stale
            </button>
          ) : null}
        </div>
      ) : null}
      <p className="mt-2 text-xs text-gray-500" aria-live="polite">
        {message}
      </p>
    </section>
  );
}
