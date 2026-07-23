"use client";

import { Fragment, useState } from "react";
import Link from "next/link";
import {
  StatusPill,
  operatorButtonClass,
  operatorTableRowClass,
} from "@/components/shared";
import type { Episode, Script } from "@/utils/api/types";
import { episodeWorkspaceHref } from "@/utils/routes";
import { ReadyCell } from "./StoryProductionDetailParts";

export function StoryEpisodeProductionRow({
  episode,
  script,
  timelineReady,
  storyboardReady,
}: {
  episode: Episode;
  script?: Script;
  timelineReady: boolean;
  storyboardReady: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const context = episode.memory_snapshot_evidence || {};
  const snapshots = Array.isArray(context.character_snapshots)
    ? (context.character_snapshots as Array<Record<string, unknown>>)
    : [];
  const disclosure = episode.disclosure_policy || {};
  return (
    <Fragment>
      <tr className={operatorTableRowClass}>
        <td className="px-5 py-4 font-medium">第{episode.episode_number}集</td>
        <td className="px-4 py-4">
          <div>{episode.title}</div>
          <button
            type="button"
            onClick={() => setExpanded((value) => !value)}
            className="mt-1 text-xs font-medium text-blue-700 underline"
          >
            {expanded ? "收起叙事证据" : "查看叙事证据"}
          </button>
        </td>
        <ReadyCell ready={Boolean(script)} />
        <ReadyCell ready={timelineReady} />
        <ReadyCell ready={storyboardReady} />
        <td className="px-5 py-4 text-right">
          <div className="flex items-center justify-end gap-2">
            {episode.memory_snapshot_stale ? (
              <StatusPill tone="red">snapshot stale</StatusPill>
            ) : null}
            <Link
              href={episodeWorkspaceHref(episode.business_id || episode.id, {
                tab: "timeline",
                scriptId: script?.id,
              })}
              className={operatorButtonClass("primary", "whitespace-nowrap")}
            >
              进入时间轴
            </Link>
          </div>
        </td>
      </tr>
      {expanded ? (
        <tr className="bg-gray-50">
          <td colSpan={6} className="px-5 py-4">
            <div className="grid gap-4 text-xs md:grid-cols-4">
              <Evidence title="起点记忆 snapshot">
                {snapshots.length
                  ? snapshots
                      .map((item) =>
                        String(item.snapshot_hash || "").slice(0, 10),
                      )
                      .join(" · ")
                  : "尚未冻结"}
              </Evidence>
              <Evidence title="来源章节锚点">
                {(episode.source_chapter_refs || [])
                  .map((item) => String(item.business_id || "").slice(0, 8))
                  .join(" · ") || "无"}
              </Evidence>
              <Evidence title="允许 / 隐藏 / 推进">
                {count(disclosure.allowed_reveal)} /{" "}
                {count(disclosure.must_hide)} / {count(disclosure.must_advance)}
              </Evidence>
              <Evidence title="本集结束角色状态">
                {episode.character_arcs
                  ? JSON.stringify(episode.character_arcs)
                  : "待剧本推进"}
              </Evidence>
            </div>
            {episode.memory_snapshot_stale ? (
              <p className="mt-3 text-xs text-red-700">
                上游来源或公共记忆基线已变化；现有生产内容不会自动替换，进入
                Timeline 前请复核。
              </p>
            ) : null}
          </td>
        </tr>
      ) : null}
    </Fragment>
  );
}

function Evidence({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="font-semibold text-gray-700">{title}</div>
      <div className="mt-1 break-words text-gray-600">{children}</div>
    </div>
  );
}

function count(value: unknown): number {
  return Array.isArray(value) ? value.length : 0;
}
