"use client";

import type { Episode, Script, Story } from "@/utils/api";
import { extractEpisodeScenes, getEpisodeSceneCount } from "@/hooks/useStoryDetail";

interface EpisodeListSectionProps {
  story: Story;
  episodes: Episode[];
  scriptsByEpisode: Record<number, Script[]>;
  loadingScripts: boolean;
  onNavigateToEpisode: (businessIdOrId: string | number) => void;
  onNavigateToStoryboard: (businessIdOrId: string | number) => void;
  onNavigateToScript: (scriptId: number) => void;
}

const normalizeEpisodeNumber = (value: unknown, fallback: number) => {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

export function EpisodeListSection({
  story,
  episodes,
  scriptsByEpisode,
  loadingScripts,
  onNavigateToEpisode,
  onNavigateToStoryboard,
  onNavigateToScript,
}: EpisodeListSectionProps) {
  const extra =
    story.extra_metadata && typeof story.extra_metadata === "object"
      ? (story.extra_metadata as Record<string, unknown>)
      : {};

  const episodeStepOutlines =
    extra && typeof extra.episode_step_outlines === "object"
      ? (extra.episode_step_outlines as Record<string, unknown>)
      : null;

  const outlineEpisodes = Array.isArray(episodeStepOutlines?.episodes)
    ? [...(episodeStepOutlines?.episodes as Record<string, unknown>[])]
        .filter(Boolean)
        .sort((a, b) => {
          const aNumRaw = a["episode_number"];
          const bNumRaw = b["episode_number"];
          const aNum = typeof aNumRaw === "number" ? aNumRaw : Number(aNumRaw || 0);
          const bNum = typeof bNumRaw === "number" ? bNumRaw : Number(bNumRaw || 0);
          return aNum - bNum;
        })
    : [];

  const combinedEpisodes = (() => {
    const outlineEntries = outlineEpisodes.map((outline, idx) => ({
      outline,
      episodeNumber: normalizeEpisodeNumber(outline["episode_number"], idx + 1),
    }));
    const episodeEntries = episodes.map((ep, idx) => ({
      episode: ep,
      episodeNumber: normalizeEpisodeNumber(ep.episode_number, idx + 1),
    }));
    const merged = new Map<
      number,
      { episodeNumber: number; episode?: Episode; outline?: Record<string, unknown> }
    >();
    outlineEntries.forEach((item) => {
      merged.set(item.episodeNumber, {
        episodeNumber: item.episodeNumber,
        outline: item.outline,
      });
    });
    episodeEntries.forEach((item) => {
      const existing = merged.get(item.episodeNumber) ?? {
        episodeNumber: item.episodeNumber,
      };
      merged.set(item.episodeNumber, { ...existing, episode: item.episode });
    });
    return Array.from(merged.values()).sort((a, b) => a.episodeNumber - b.episodeNumber);
  })();

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">剧集列表</h2>
        <span className="text-sm text-gray-500">共 {combinedEpisodes.length} 集</span>
      </div>

      {combinedEpisodes.length === 0 ? (
        <div className="text-center py-10 text-gray-500">暂无剧集</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {combinedEpisodes.map(({ episode, outline, episodeNumber }) => (
            <EpisodeCard
              key={`episode-${episodeNumber}`}
              episode={episode}
              outline={outline}
              episodeNumber={episodeNumber}
              scripts={episode ? scriptsByEpisode[episode.id] || [] : []}
              loadingScripts={loadingScripts}
              onNavigateToEpisode={onNavigateToEpisode}
              onNavigateToStoryboard={onNavigateToStoryboard}
              onNavigateToScript={onNavigateToScript}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface EpisodeCardProps {
  episode?: Episode;
  outline?: Record<string, unknown>;
  episodeNumber: number;
  scripts: Script[];
  loadingScripts: boolean;
  onNavigateToEpisode: (businessIdOrId: string | number) => void;
  onNavigateToStoryboard: (businessIdOrId: string | number) => void;
  onNavigateToScript: (scriptId: number) => void;
}

function EpisodeCard({
  episode,
  outline,
  episodeNumber,
  scripts,
  loadingScripts,
  onNavigateToEpisode,
  onNavigateToStoryboard,
  onNavigateToScript,
}: EpisodeCardProps) {
  const scenes = episode ? extractEpisodeScenes(episode) : [];
  const sceneCount = episode ? getEpisodeSceneCount(episode) : undefined;

  const titleFromEpisode = episode?.title?.trim();
  const titleFromOutline =
    typeof outline?.["title"] === "string" && (outline["title"] as string).trim()
      ? (outline["title"] as string)
      : "";
  const title = titleFromEpisode || titleFromOutline || `第${episodeNumber}集`;

  const summaryFromOutline =
    typeof outline?.["logline"] === "string" && (outline["logline"] as string).trim()
      ? (outline["logline"] as string)
      : "";
  const summary = episode?.summary || summaryFromOutline || "暂无概要";

  const beats = Array.isArray(outline?.["beats"])
    ? (outline?.["beats"] as Record<string, unknown>[])
    : [];

  return (
    <div className="border rounded-lg p-4 hover:bg-gray-50">
      <div className="flex items-center justify-between gap-2">
        <div className="font-medium text-gray-900">
          第{episodeNumber}集 · {title}
        </div>
        {episode && (
          <button
            onClick={() => onNavigateToEpisode(episode.business_id || episode.id)}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            查看
          </button>
        )}
      </div>
      <div className="text-sm text-gray-600 mt-2 line-clamp-3">{summary}</div>
      <div className="flex items-center gap-4 text-xs text-gray-500 mt-3">
        <span>时长：{episode?.duration_minutes || "--"} 分钟</span>
        <span>场景：{sceneCount || "--"}</span>
        <span>剧本：{loadingScripts ? "加载中..." : scripts.length}</span>
      </div>

      {beats.length > 0 && (
        <BeatsPreview beats={beats} episodeNumber={episodeNumber} />
      )}

      {scenes.length > 0 && (
        <ScenesPreview scenes={scenes} />
      )}

      {scripts.length > 0 && episode && (
        <ScriptsPreview
          scripts={scripts}
          episode={episode}
          onNavigateToStoryboard={onNavigateToStoryboard}
          onNavigateToScript={onNavigateToScript}
        />
      )}
    </div>
  );
}

function BeatsPreview({
  beats,
  episodeNumber,
}: {
  beats: Record<string, unknown>[];
  episodeNumber: number;
}) {
  return (
    <div className="mt-3 space-y-1 text-xs text-gray-700">
      <div className="text-gray-500">大纲情节点</div>
      {beats.slice(0, 3).map((beat, bIdx) => {
        const seqRaw = beat?.["sequence_number"];
        const seq = typeof seqRaw === "number" ? seqRaw : bIdx + 1;
        const beatTitle =
          typeof beat?.["beat_title"] === "string" && (beat["beat_title"] as string).trim()
            ? (beat["beat_title"] as string)
            : typeof beat?.["beat_summary"] === "string"
              ? (beat["beat_summary"] as string)
              : `节点 ${seq}`;
        return (
          <div
            key={`beat-${episodeNumber}-${seq}`}
            className="flex items-center justify-between"
          >
            <span className="font-medium text-gray-800">节点 {seq}</span>
            <span className="text-[11px] text-gray-500 truncate max-w-[220px]">
              {beatTitle}
            </span>
          </div>
        );
      })}
      {beats.length > 3 && (
        <div className="text-[11px] text-gray-400">
          还有 {beats.length - 3} 个节点…
        </div>
      )}
    </div>
  );
}

function ScenesPreview({ scenes }: { scenes: Record<string, unknown>[] }) {
  return (
    <div className="mt-3 space-y-1 text-xs text-gray-600">
      <div className="text-gray-500">场景预览</div>
      {scenes.slice(0, 3).map((scene, idx) => {
        const rawNo = scene.scene_number;
        const sceneNumber =
          typeof rawNo === "number" ? rawNo : parseInt(String(rawNo ?? idx + 1), 10);
        const sceneLabel = Number.isFinite(sceneNumber) ? sceneNumber : idx + 1;
        const titleRaw = scene.slug_line ?? scene.summary ?? scene.description;
        const title = typeof titleRaw === "string" ? titleRaw : `场景 ${sceneLabel}`;
        return (
          <div key={`scene-${sceneLabel}`} className="flex items-center justify-between gap-2">
            <span className="font-medium text-gray-800">场景 {sceneLabel}</span>
            <span className="text-[11px] text-gray-500 truncate">{String(title)}</span>
          </div>
        );
      })}
      {scenes.length > 3 && (
        <div className="text-[11px] text-gray-400">
          还有 {scenes.length - 3} 个场景…
        </div>
      )}
    </div>
  );
}

function ScriptsPreview({
  scripts,
  episode,
  onNavigateToStoryboard,
  onNavigateToScript,
}: {
  scripts: Script[];
  episode: Episode;
  onNavigateToStoryboard: (businessIdOrId: string | number) => void;
  onNavigateToScript: (scriptId: number) => void;
}) {
  return (
    <div className="mt-3 text-sm">
      <div className="text-gray-700 mb-1 flex items-center justify-between">
        <span>最新剧本：</span>
        <button
          onClick={() => onNavigateToStoryboard(episode.business_id || episode.id)}
          className="text-blue-600 hover:text-blue-800 text-xs"
        >
          分镜管理
        </button>
      </div>
      <div className="space-y-1">
        {scripts.slice(0, 2).map((sc) => (
          <div key={sc.id} className="flex items-center justify-between">
            <div className="truncate mr-2">{sc.title}</div>
            <button
              onClick={() => onNavigateToScript(sc.id)}
              className="text-blue-600 hover:text-blue-800 text-xs"
            >
              查看
            </button>
          </div>
        ))}
        {scripts.length > 2 && (
          <div className="text-xs text-gray-500">
            还有 {scripts.length - 2} 个剧本…
          </div>
        )}
      </div>
    </div>
  );
}
