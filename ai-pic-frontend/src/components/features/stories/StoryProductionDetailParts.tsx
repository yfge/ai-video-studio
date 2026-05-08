"use client";

import { StatusPill } from "@/components/shared";
import type { StoryCharacter, VirtualIPEnvironmentLink } from "@/utils/api/types";

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
  const name = character.character_name || character.name || "未命名 IP";
  return (
    <span className="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs text-gray-600">
      IP: {name}
    </span>
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
