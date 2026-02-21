"use client";

import type { Episode } from "@/utils/api/types";

interface PlotPoint {
  timing?: string;
  description?: string;
}

interface Conflict {
  intensity?: string;
  description?: string;
}

interface WorkspaceOverviewTabContentProps {
  episode: Episode;
  scriptSceneCount?: number;
}

export function WorkspaceOverviewTabContent({
  episode,
  scriptSceneCount,
}: WorkspaceOverviewTabContentProps) {
  // Parse plot_points
  const plotPoints: PlotPoint[] = Array.isArray(episode.plot_points)
    ? episode.plot_points.map((p) => {
        if (typeof p === "object" && p !== null) return p as PlotPoint;
        if (typeof p === "string") return { description: p };
        return { description: JSON.stringify(p) };
      })
    : [];

  // Parse conflicts
  const conflicts: Conflict[] = Array.isArray(episode.conflicts)
    ? episode.conflicts.map((c) => {
        if (typeof c === "object" && c !== null) return c as Conflict;
        if (typeof c === "string") return { description: c };
        return { description: JSON.stringify(c) };
      })
    : [];

  // Parse character_arcs
  const characterArcs = episode.character_arcs || {};
  const sceneCount =
    typeof scriptSceneCount === "number" && scriptSceneCount >= 0
      ? scriptSceneCount
      : episode.scene_count;

  return (
    <div className="space-y-6">
      {/* Basic Info Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">基本信息</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <span className="text-sm text-gray-500">集数</span>
            <p className="text-lg font-medium">
              第 {episode.episode_number} 集
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-500">时长</span>
            <p className="text-lg font-medium">
              {episode.duration_minutes || "—"} 分钟
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-500">场景数</span>
            <p className="text-lg font-medium">{sceneCount || "—"} 个</p>
          </div>
          <div>
            <span className="text-sm text-gray-500">状态</span>
            <p className="text-lg font-medium">
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  episode.status === "published"
                    ? "bg-green-100 text-green-800"
                    : episode.status === "draft"
                    ? "bg-yellow-100 text-yellow-800"
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                {episode.status === "published"
                  ? "已发布"
                  : episode.status === "draft"
                  ? "草稿"
                  : episode.status}
              </span>
            </p>
          </div>
        </div>
      </div>

      {/* Summary Card */}
      {episode.summary && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">剧集概要</h3>
          <p className="text-gray-700 whitespace-pre-wrap">{episode.summary}</p>
        </div>
      )}

      {/* Plot Points Card */}
      {plotPoints.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">剧情要点</h3>
          <ul className="space-y-2">
            {plotPoints.map((point, index) => (
              <li key={index} className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-600 text-sm flex items-center justify-center">
                  {index + 1}
                </span>
                <div className="flex-1">
                  {point.timing && (
                    <span className="text-xs font-medium text-blue-600 mr-2">
                      {point.timing}
                    </span>
                  )}
                  <span className="text-gray-700">{point.description}</span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Conflicts Card */}
      {conflicts.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">冲突点</h3>
          <ul className="space-y-2">
            {conflicts.map((conflict, index) => (
              <li key={index} className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-red-100 text-red-600 text-sm flex items-center justify-center">
                  !
                </span>
                <div className="flex-1">
                  {conflict.intensity && (
                    <span
                      className={`text-xs font-medium mr-2 px-1.5 py-0.5 rounded ${
                        conflict.intensity === "高"
                          ? "bg-red-100 text-red-700"
                          : conflict.intensity === "中"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {conflict.intensity}
                    </span>
                  )}
                  <span className="text-gray-700">{conflict.description}</span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Character Arcs Card */}
      {Object.keys(characterArcs).length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">角色弧线</h3>
          <div className="space-y-3">
            {Object.entries(characterArcs).map(([character, arc]) => (
              <div
                key={character}
                className="border-l-4 border-purple-400 pl-4"
              >
                <h4 className="font-medium text-gray-900">{character}</h4>
                <p className="text-gray-600 text-sm">
                  {typeof arc === "string" ? arc : JSON.stringify(arc)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tags Card */}
      {episode.tags && episode.tags.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">标签</h3>
          <div className="flex flex-wrap gap-2">
            {episode.tags.map((tag, index) => (
              <span
                key={index}
                className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Metadata Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">元数据</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">创建时间</span>
            <p className="text-gray-900">
              {new Date(episode.created_at).toLocaleString("zh-CN")}
            </p>
          </div>
          <div>
            <span className="text-gray-500">更新时间</span>
            <p className="text-gray-900">
              {new Date(episode.updated_at).toLocaleString("zh-CN")}
            </p>
          </div>
          {episode.ai_model && (
            <div>
              <span className="text-gray-500">生成模型</span>
              <p className="text-gray-900">{episode.ai_model}</p>
            </div>
          )}
          <div>
            <span className="text-gray-500">业务ID</span>
            <p className="text-gray-900 font-mono text-xs">
              {episode.business_id}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
