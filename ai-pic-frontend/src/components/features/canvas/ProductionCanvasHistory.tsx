"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  OperatorPanel,
  OperatorSectionHeader,
  OperatorShell,
  OperatorState,
  operatorButtonClass,
} from "@/components/shared";
import { taskAPI } from "@/utils/api/endpoints";
import type { Task } from "@/utils/api/types";

const CANVAS_RUN_KIND = "production_canvas_run";
const HISTORY_PAGE_SIZE = 100;

export type ProductionCanvasHistoryItem = {
  nodeCount: number;
  runId: string;
  title: string;
  updatedAt: string;
};

const record = (value: unknown): Record<string, unknown> =>
  value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};

const text = (value: unknown) =>
  typeof value === "string" ? value.trim() : "";

function historyItem(task: Task): ProductionCanvasHistoryItem | null {
  const parameters = record(task.parameters);
  if (parameters.kind !== CANVAS_RUN_KIND || !task.business_id) return null;
  const savedState = record(parameters.saved_state);
  const nodes = Array.isArray(savedState.nodes)
    ? savedState.nodes
    : Array.isArray(parameters.nodes)
    ? parameters.nodes
    : [];
  return {
    nodeCount: nodes.length,
    runId: task.business_id,
    title: text(parameters.prompt) || text(task.prompt) || "未命名画布",
    updatedAt: task.updated_at || task.created_at,
  };
}

export async function loadProductionCanvasHistory() {
  const tasks: Task[] = [];
  let page = 1;
  let total = 0;
  do {
    const response = await taskAPI.getTasks({
      page,
      size: HISTORY_PAGE_SIZE,
      task_type: "text_generation",
    });
    if (!response.success || !response.data) {
      throw new Error(response.error || "历史画布加载失败");
    }
    tasks.push(...response.data.tasks);
    total = response.data.total;
    if (!response.data.tasks.length) break;
    page += 1;
  } while ((page - 1) * HISTORY_PAGE_SIZE < total);

  return tasks
    .map(historyItem)
    .filter((item): item is ProductionCanvasHistoryItem => item !== null)
    .sort(
      (left, right) => Date.parse(right.updatedAt) - Date.parse(left.updatedAt),
    );
}

function formatUpdatedAt(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function ProductionCanvasHistoryContent({
  error,
  items,
  loading,
  onRetry,
}: {
  error: string | null;
  items: ProductionCanvasHistoryItem[];
  loading: boolean;
  onRetry?: () => void;
}) {
  return (
    <OperatorPanel className="overflow-hidden">
      <OperatorSectionHeader
        title="历史画布"
        subtitle="按最近更新时间排列，打开后继续编辑已有画布"
        action={
          <Link href="/canvas?new=1" className={operatorButtonClass("primary")}>
            新建空白画布
          </Link>
        }
      />
      <div className="p-4">
        {loading ? (
          <OperatorState title="正在加载历史画布" detail="请稍候…" />
        ) : error ? (
          <OperatorState
            title="历史画布加载失败"
            detail={error}
            tone="red"
            action={
              onRetry ? (
                <button
                  type="button"
                  className={operatorButtonClass("secondary")}
                  onClick={onRetry}
                >
                  重新加载
                </button>
              ) : null
            }
          />
        ) : items.length ? (
          <ul className="divide-y divide-gray-100" aria-label="历史画布">
            {items.map((item) => (
              <li key={item.runId}>
                <Link
                  href={`/canvas?run_id=${encodeURIComponent(item.runId)}`}
                  data-canvas-history-run={item.runId}
                  className="grid gap-2 px-3 py-4 transition-colors hover:bg-blue-50/50 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center"
                >
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold text-gray-950">
                      {item.title}
                    </div>
                    <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-gray-500">
                      <span>{item.nodeCount} 个节点</span>
                      <span className="font-mono">{item.runId}</span>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500">
                    更新于 {formatUpdatedAt(item.updatedAt)}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <OperatorState
            title="还没有历史画布"
            detail="新建空白画布，第一次生成生产计划后会自动保存到这里。"
          />
        )}
      </div>
    </OperatorPanel>
  );
}

export function ProductionCanvasHistory() {
  const [items, setItems] = useState<ProductionCanvasHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    void loadProductionCanvasHistory()
      .then((history) => {
        if (active) setItems(history);
      })
      .catch((reason) => {
        if (active)
          setError(reason instanceof Error ? reason.message : String(reason));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [reloadToken]);

  return (
    <OperatorShell
      title="创作画布"
      subtitle="选择历史画布继续创作，或从空白画布开始"
      breadcrumb={["IP 中心", "创作画布"]}
      showGlobalSearch={false}
    >
      <ProductionCanvasHistoryContent
        error={error}
        items={items}
        loading={loading}
        onRetry={() => setReloadToken((current) => current + 1)}
      />
    </OperatorShell>
  );
}
