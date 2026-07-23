"use client";

import {
  OperatorMainCanvas,
  OperatorPanel,
  OperatorState,
  OperatorTabs,
  OperatorWorkspace,
  StatusPill,
  operatorButtonClass,
} from "@/components/shared";
import { useStoryMemoryWorkspace } from "@/hooks/useStoryMemoryWorkspace";
import type {
  MemoryWorkspaceItem,
  MemoryWorkspaceTab,
} from "@/hooks/useStoryMemoryWorkspace";
import { StoryMemoryInspector } from "./StoryMemoryInspector";
import {
  GrowthView,
  MemoryFilterPanel,
  MemoryItemList,
} from "./StoryMemoryViews";

const TABS: Array<{ key: MemoryWorkspaceTab; label: string }> = [
  { key: "events", label: "事件与事实" },
  { key: "memories", label: "角色记忆" },
  { key: "growth", label: "成长轨迹" },
  { key: "review", label: "审核队列" },
];

export function StoryMemoryWorkspace({ storyId }: { storyId: string }) {
  const state = useStoryMemoryWorkspace(storyId);
  if (state.loading) return <OperatorState title="正在加载叙事记忆…" />;
  if (state.error || !state.story) {
    return (
      <OperatorState title={state.error || "故事不存在或无权访问"} tone="red" />
    );
  }
  const characters =
    state.story.story_characters || state.story.characters || [];
  const items: MemoryWorkspaceItem[] =
    state.tab === "events"
      ? state.events
      : state.tab === "review"
      ? state.reviewItems
      : state.memories;

  return (
    <OperatorWorkspace
      variant="main-inspector"
      main={
        <OperatorMainCanvas className="space-y-4">
          <MemoryHeader state={state} />
          <div className="grid gap-4 lg:grid-cols-[220px_minmax(0,1fr)]">
            <MemoryFilterPanel state={state} characters={characters} />
            <OperatorPanel>
              <div className="border-b border-gray-100 p-3">
                <OperatorTabs
                  tabs={TABS}
                  active={state.tab}
                  onChange={state.setTab}
                />
              </div>
              {state.tab === "growth" ? (
                <GrowthView items={state.memories} />
              ) : (
                <MemoryItemList
                  items={items}
                  selectedId={state.selected?.business_id}
                  onSelect={state.setSelectedId}
                />
              )}
            </OperatorPanel>
          </div>
        </OperatorMainCanvas>
      }
      inspector={
        <StoryMemoryInspector
          item={state.selected}
          anchors={state.anchors}
          onSave={state.save}
          onReview={state.review}
          onSplit={state.split}
          onMerge={state.merge}
          onPromote={state.promote}
        />
      }
    />
  );
}

function MemoryHeader({
  state,
}: {
  state: ReturnType<typeof useStoryMemoryWorkspace>;
}) {
  const summary = state.summary;
  return (
    <OperatorPanel className="p-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-lg font-semibold">
            {state.story?.title} · 叙事记忆
          </h1>
          <div className="mt-2 flex flex-wrap gap-2">
            <StatusPill tone="blue">
              branch {summary?.canon_branch_id || "main"}
            </StatusPill>
            <StatusPill tone="gray">
              私有 {summary?.private_memory_count || 0}
            </StatusPill>
            <StatusPill tone={summary?.pending_count ? "amber" : "gray"}>
              待审核 {summary?.pending_count || 0}
            </StatusPill>
            <StatusPill tone={summary?.stale_count ? "red" : "gray"}>
              stale {summary?.stale_count || 0}
            </StatusPill>
            <StatusPill tone="gray">
              snapshot {summary?.latest_snapshot_hash?.slice(0, 8) || "未构建"}
            </StatusPill>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void state.extract("story_seed")}
            className={operatorButtonClass("secondary")}
          >
            从 Story Seed 提取
          </button>
          <button
            type="button"
            onClick={() => void state.extract("canonical_novel")}
            className={operatorButtonClass("primary")}
          >
            从审批小说提取（可能调用模型）
          </button>
        </div>
      </div>
      <p className="mt-3 text-xs text-gray-500" aria-live="polite">
        {state.taskMessage ||
          "查看、筛选和审核不调用模型；提取按钮会创建显式异步任务。"}
      </p>
    </OperatorPanel>
  );
}
