"use client";

import type { Episode } from "@/utils/api";
import { asRecord, extractScenes, getString } from "@/hooks/useEpisodeDetail";

interface EpisodeDetailsProps {
  episode: Episode;
}

export function EpisodeDetails({ episode }: EpisodeDetailsProps) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-xl font-semibold mb-4">剧集详情</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h3 className="font-medium text-gray-900 mb-2">剧集概要</h3>
          <p className="text-gray-600 mb-4">{episode.summary || "暂无概要"}</p>

          <h3 className="font-medium text-gray-900 mb-2">主要情节点</h3>
          {episode.plot_points && episode.plot_points.length > 0 ? (
            <div className="space-y-2">
              {episode.plot_points.map((point, idx) => {
                const record = asRecord(point);
                const description =
                  getString(record?.description) ??
                  (typeof point === "string" ? point : `情节点 ${idx + 1}`);
                const timing = getString(record?.timing);
                const purpose = getString(record?.purpose);
                const escalation = getString(record?.escalation);
                return (
                  <div key={idx} className="bg-gray-50 p-3 rounded">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-medium text-gray-900">
                        {description}
                      </div>
                      {timing && (
                        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
                          {timing}
                        </span>
                      )}
                    </div>
                    {(purpose || escalation) && (
                      <div className="mt-1 text-xs text-gray-600">
                        {purpose && <div>目的：{purpose}</div>}
                        {escalation && <div>升级：{escalation}</div>}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">暂无情节点</p>
          )}
        </div>

        <div>
          <h3 className="font-medium text-gray-900 mb-2">角色发展</h3>
          <div className="text-sm text-gray-600 mb-4">
            {episode.character_arcs &&
            Object.keys(episode.character_arcs).length > 0 ? (
              Object.entries(episode.character_arcs).map(([character, arc]) => (
                <div key={character} className="mb-2">
                  <span className="font-medium">{character}:</span> {String(arc)}
                </div>
              ))
            ) : (
              <p className="text-gray-500">暂无角色发展信息</p>
            )}
          </div>

          <h3 className="font-medium text-gray-900 mb-2">冲突设置</h3>
          {episode.conflicts && episode.conflicts.length > 0 ? (
            <div className="space-y-2">
              {episode.conflicts.map((conflict, idx) => {
                const record = asRecord(conflict);
                const description =
                  getString(record?.description) ??
                  (typeof conflict === "string" ? conflict : `冲突 ${idx + 1}`);
                const intensity = getString(record?.intensity);
                const partiesRaw = record?.parties;
                const parties = Array.isArray(partiesRaw)
                  ? partiesRaw
                      .map((part) => getString(part))
                      .filter((part): part is string => Boolean(part))
                  : [];
                const intensityClass =
                  intensity === "high"
                    ? "bg-red-200 text-red-800"
                    : intensity === "medium"
                    ? "bg-yellow-200 text-yellow-800"
                    : "bg-gray-200 text-gray-800";
                return (
                  <div key={idx} className="bg-red-50 p-3 rounded text-sm">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-red-900">{description}</span>
                      {intensity && (
                        <span className={`text-xs px-2 py-0.5 rounded ${intensityClass}`}>
                          {intensity}
                        </span>
                      )}
                    </div>
                    {parties.length > 0 && (
                      <div className="mt-1 text-xs text-gray-700">
                        涉及：{parties.join(" vs ")}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">暂无冲突设置</p>
          )}
        </div>
      </div>

      {/* Scene list */}
      <div className="mt-6">
        <h3 className="font-medium text-gray-900 mb-2">场景列表</h3>
        {extractScenes(episode).length === 0 ? (
          <p className="text-gray-500 text-sm">
            暂无场景数据（可重新生成剧集后刷新）。
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {extractScenes(episode).map((scene: Record<string, unknown>, idx: number) => {
              const title =
                (scene.title as string) ||
                (scene.slug_line as string) ||
                `场景 ${idx + 1}`;
              const desc =
                (scene.summary as string) ||
                (scene.description as string) ||
                (scene.beat_summary as string);
              const loc =
                (scene.location as string) ||
                (scene.environment as string) ||
                (scene.setting as string);
              const tod =
                (scene.time_of_day as string) ||
                (scene.time as string) ||
                (scene.period as string);
              const status = scene.status as string | undefined;
              const sceneNumber =
                (scene as { scene_number?: number | string }).scene_number ?? idx + 1;
              return (
                <div key={idx} className="border rounded p-3 bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="font-medium text-gray-900">场景 {sceneNumber}</div>
                    {status && <span className="text-xs text-gray-600">{status}</span>}
                  </div>
                  <div className="text-sm text-gray-800 mt-1">{title}</div>
                  {desc && (
                    <div className="text-xs text-gray-600 mt-1 line-clamp-3">{desc}</div>
                  )}
                  {(loc || tod) && (
                    <div className="text-xs text-gray-500 mt-2">
                      {loc ? `地点：${loc}` : ""} {tod ? ` · 时间：${tod}` : ""}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
