import { OperatorPanel, OperatorState, StatusPill } from "@/components/shared";
import { useStoryMemoryWorkspace } from "@/hooks/useStoryMemoryWorkspace";
import type { MemoryWorkspaceItem } from "@/hooks/useStoryMemoryWorkspace";
import type {
  CharacterMemory,
  NarrativeEvent,
  StoryCharacter,
} from "@/utils/api/types";

type WorkspaceState = ReturnType<typeof useStoryMemoryWorkspace>;

export function MemoryFilterPanel({
  state,
  characters,
}: {
  state: WorkspaceState;
  characters: StoryCharacter[];
}) {
  return (
    <OperatorPanel className="space-y-4 p-4">
      <h2 className="text-sm font-semibold">过滤与导航</h2>
      <Select
        label="角色"
        value={state.characterId}
        onChange={state.setCharacterId}
        options={characters.map((item) => [
          item.business_id,
          item.display_name ||
            item.character_name ||
            item.business_id.slice(0, 8),
        ])}
      />
      <Select
        label="状态"
        value={state.status}
        onChange={state.setStatus}
        options={[
          ["candidate", "候选"],
          ["approved", "已批准"],
          ["rejected", "已拒绝"],
          ["stale", "stale"],
        ]}
      />
      <Select
        label="事件类型"
        value={state.eventType}
        onChange={state.setEventType}
        options={[
          ["action", "行动"],
          ["reveal", "揭示"],
          ["relationship", "关系"],
          ["state_change", "状态变化"],
          ["world_fact", "世界事实"],
        ]}
      />
      <Select
        label="观众显隐"
        value={state.disclosure}
        onChange={state.setDisclosure}
        options={[
          ["hidden", "隐藏"],
          ["hinted", "暗示"],
          ["partial", "部分"],
          ["revealed", "已揭示"],
        ]}
      />
    </OperatorPanel>
  );
}

function Select({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<[string, string]>;
}) {
  return (
    <label className="block text-xs font-medium text-gray-600">
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 w-full rounded-md border border-gray-300 px-2 py-2 text-sm"
      >
        <option value="">全部</option>
        {options.map(([key, text]) => (
          <option key={key} value={key}>
            {text}
          </option>
        ))}
      </select>
    </label>
  );
}

export function MemoryItemList({
  items,
  selectedId,
  onSelect,
}: {
  items: MemoryWorkspaceItem[];
  selectedId?: string;
  onSelect: (id: string) => void;
}) {
  if (!items.length) {
    return (
      <OperatorState
        title="尚无匹配内容"
        detail="尚未提取不等于没有连续性问题。"
      />
    );
  }
  return (
    <div className="divide-y divide-gray-100">
      {items.map((item) => (
        <button
          type="button"
          key={item.business_id}
          onClick={() => onSelect(item.business_id)}
          className={`block w-full p-4 text-left focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 ${
            selectedId === item.business_id ? "bg-blue-50" : "hover:bg-gray-50"
          }`}
        >
          <div className="flex justify-between gap-3">
            <span className="text-sm font-medium text-gray-900">
              {isEvent(item) ? item.summary : item.content}
            </span>
            <StatusPill
              tone={
                item.status === "approved"
                  ? "green"
                  : item.status === "stale"
                  ? "red"
                  : "amber"
              }
            >
              {item.status}
            </StatusPill>
          </div>
          <p className="mt-2 text-xs text-gray-500">
            {isEvent(item)
              ? `${item.presentation} · ${item.audience_disclosure}`
              : `${
                  item.memory_type
                } · 生效 ${item.effective_from_anchor_business_id.slice(0, 8)}`}
          </p>
        </button>
      ))}
    </div>
  );
}

export function GrowthView({ items }: { items: MemoryWorkspaceItem[] }) {
  const memories = items.filter(isMemory);
  if (!memories.length) return <OperatorState title="尚无成长记忆" />;
  return (
    <div className="space-y-3 p-4">
      {memories.map((item) => (
        <div
          key={item.business_id}
          className="rounded-md border border-gray-200 p-3"
        >
          <div className="text-sm font-medium">{item.content}</div>
          <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-500">
            {item.emotional_impact.map((emotion) => (
              <span key={emotion}>#{emotion}</span>
            ))}
            {item.belief ? <span>信念：{item.belief}</span> : null}
          </div>
        </div>
      ))}
    </div>
  );
}

function isEvent(item: MemoryWorkspaceItem): item is NarrativeEvent {
  return "event_type" in item;
}

function isMemory(item: MemoryWorkspaceItem): item is CharacterMemory {
  return !isEvent(item);
}
