"use client";

import {
  OperatorPanel,
  OperatorSectionHeader,
  StatusPill,
} from "@/components/shared";
import type {
  Story,
  StoryCharacter,
  VirtualIPEnvironmentLink,
} from "@/utils/api/types";

const STORY_OUTLINE_TEXT_FIELDS = [
  ["目标观众", "target_audience"],
  ["核心情绪痛点", "core_emotional_pain"],
  ["故事大期待", "big_expectation"],
  ["主角目标", "protagonist_goal"],
  ["结构冲突", "structural_conflict"],
  ["信息差", "information_gap"],
  ["前三集主线", "first_three_episode_spine"],
  ["拍摄可行性", "shootability"],
] as const;

const STORY_OUTLINE_LIST_FIELDS = [
  ["阶段期待", "small_expectation_ladder"],
  ["阶段高潮", "stage_highs"],
  ["投流钩子", "traffic_hooks"],
  ["合规风险", "compliance_risks"],
] as const;

export function StoryOutlineSection({ story }: { story: Story }) {
  const raw = story.extra_metadata?.structured_story_contract;
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
  const contract = raw as Record<string, unknown>;

  return (
    <OperatorPanel>
      <OperatorSectionHeader
        title="1. 故事合同"
        subtitle="新生产故事的结构化创作合同"
      />
      <div className="grid gap-4 p-5 md:grid-cols-2">
        {STORY_OUTLINE_TEXT_FIELDS.map(([label, key]) => {
          const value = contract[key];
          if (typeof value !== "string" || !value.trim()) return null;
          return (
            <div key={key}>
              <div className="text-xs font-medium text-gray-500">{label}</div>
              <p className="mt-1 whitespace-pre-wrap text-sm leading-6 text-gray-800">
                {value}
              </p>
            </div>
          );
        })}
      </div>
      <div className="grid gap-4 border-t border-gray-100 p-5 md:grid-cols-2">
        {STORY_OUTLINE_LIST_FIELDS.map(([label, key]) => {
          const values = Array.isArray(contract[key])
            ? contract[key].filter(
                (value): value is string =>
                  typeof value === "string" && Boolean(value.trim()),
              )
            : [];
          if (!values.length) return null;
          return (
            <div key={key}>
              <div className="text-xs font-medium text-gray-500">{label}</div>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-gray-800">
                {values.map((value, index) => (
                  <li key={`${key}-${index}`}>{value}</li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </OperatorPanel>
  );
}

export function ReadyCell({ ready }: { ready: boolean }) {
  return (
    <td className="px-4 py-4">
      <StatusPill tone={ready ? "green" : "gray"}>
        {ready ? "已就绪" : "未开始"}
      </StatusPill>
    </td>
  );
}

export function CharacterChip({ character }: { character: StoryCharacter }) {
  const name = storyCharacterDisplayName(character, "未命名 IP");
  return (
    <span className="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs text-gray-600">
      IP: {name}
    </span>
  );
}

export function storyCharacterDisplayName(
  character: StoryCharacter,
  fallback = "未命名",
) {
  return (
    [
      character.character_name,
      character.display_name,
      character.name,
      character.virtual_ip_name,
    ]
      .find((value) => typeof value === "string" && value.trim())
      ?.trim() || fallback
  );
}

export function StoryEnvironmentCoverage({
  links,
}: {
  links: VirtualIPEnvironmentLink[];
}) {
  const unique = new Map<number, VirtualIPEnvironmentLink>();
  links.forEach((link) => unique.set(link.environment_id, link));
  const items = Array.from(unique.values());

  if (!items.length) {
    return (
      <span className="rounded-md border border-amber-200 bg-amber-50 px-2 py-1 text-xs text-amber-700">
        环境待接入
      </span>
    );
  }

  return (
    <>
      <span className="rounded-md border border-green-200 bg-green-50 px-2 py-1 text-xs text-green-700">
        环境资产 {items.length} 个
      </span>
      {items.slice(0, 3).map((link) => (
        <span
          key={link.environment_id}
          className="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs text-gray-600"
        >
          场景: {link.environment.name}
        </span>
      ))}
    </>
  );
}
