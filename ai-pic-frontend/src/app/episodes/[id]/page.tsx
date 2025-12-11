"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { episodeAPI, scriptAPI } from "@/utils/api";
import type { Episode, Script, ScriptGenerationRequest } from "@/utils/api";
import { useAlertModal } from "@/components/AlertModalProvider";
import { MultiModelSelector } from "@/components/MultiModelSelector";

export default function EpisodeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const episodeId = Number(params.id);
  const { showAlert } = useAlertModal();

  const [episode, setEpisode] = useState<Episode | null>(null);
  const [scripts, setScripts] = useState<Script[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [showGenerateForm, setShowGenerateForm] = useState(false);
  const [useAsync, setUseAsync] = useState(true);
  const [promptPreview, setPromptPreview] = useState("");

  // 剧本生成表单状态
  const [generateForm, setGenerateForm] = useState<ScriptGenerationRequest>({
    episode_id: episodeId,
    format_type: "screenplay",
    language: "zh-CN",
    dialogue_style: "natural",
    scene_detail_level: "medium",
    additional_requirements: "",
    style_preferences: [],
  });

  const [formats, setFormats] = useState<
    Array<{ value: string; label: string }>
  >([]);
  const [languages, setLanguages] = useState<
    Array<{ value: string; label: string }>
  >([]);
  const asRecord = (value: unknown): Record<string, unknown> | null =>
    value && typeof value === "object"
      ? (value as Record<string, unknown>)
      : null;
  const getString = (value: unknown): string | undefined =>
    typeof value === "string" ? value : undefined;
  const extractScenes = (ep: Episode | null): Record<string, unknown>[] => {
    if (!ep) return [];
    const meta =
      (ep as unknown as Record<string, unknown>)?.extra_metadata ??
      ep.metadata ??
      {};
    const scenes = (meta as Record<string, unknown>)?.scenes;
    if (Array.isArray(scenes)) {
      return scenes.filter(
        (s): s is Record<string, unknown> =>
          Boolean(s) && typeof s === "object",
      );
    }
    return [];
  };
  const getSceneCount = (ep: Episode | null): number | undefined => {
    if (!ep) return undefined;
    const scenes = extractScenes(ep);
    const fallback = scenes.length > 0 ? scenes.length : undefined;
    return ep.scene_count ?? fallback;
  };

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [episodeResponse, scriptsResponse] = await Promise.all([
        episodeAPI.getEpisode(episodeId),
        scriptAPI.getEpisodeScripts(episodeId),
      ]);

      if (episodeResponse.success && episodeResponse.data) {
        setEpisode(episodeResponse.data);
      }
      if (scriptsResponse.success && scriptsResponse.data) {
        setScripts(scriptsResponse.data);
      }
    } catch (error) {
      console.error("加载数据失败:", error);
      showAlert({ message: "加载数据失败", variant: "error" });
    } finally {
      setLoading(false);
    }
  }, [episodeId, showAlert]);

  const loadOptions = useCallback(async () => {
    try {
      const [formatsResponse, languagesResponse] = await Promise.all([
        scriptAPI.getScriptFormats(),
        scriptAPI.getScriptLanguages(),
      ]);

      if (formatsResponse.success && formatsResponse.data) {
        setFormats(formatsResponse.data);
      }
      if (languagesResponse.success && languagesResponse.data) {
        setLanguages(languagesResponse.data);
      }
    } catch (error) {
      console.error("加载选项失败:", error);
    }
  }, []);

  useEffect(() => {
    void loadData();
    void loadOptions();
  }, [loadData, loadOptions]);

  useEffect(() => {
    setGenerateForm((prev) => ({ ...prev, episode_id: episodeId }));
  }, [episodeId]);

  const handleGenerateScript = async () => {
    try {
      setGenerating(true);
      if (useAsync) {
        const response = await scriptAPI.generateScriptAsync(generateForm);
        if (response.success) {
          showAlert({
            message: "已创建任务，请稍后在任务页查看进度",
            variant: "info",
          });
        } else {
          showAlert({
            message: `剧本生成失败：${response.error || "未知错误"}`,
            variant: "error",
          });
        }
      } else {
        const response = await scriptAPI.generateScript(generateForm);
        if (response.success && response.data) {
          setScripts((prev) => [response.data as Script, ...prev]);
          setShowGenerateForm(false);
          showAlert({ message: "剧本生成成功！", variant: "success" });
        } else {
          showAlert({
            message: `剧本生成失败：${response.error || "未知错误"}`,
            variant: "error",
          });
        }
      }
    } catch (error) {
      console.error("剧本生成失败:", error);
      showAlert({ message: "剧本生成失败", variant: "error" });
    } finally {
      setGenerating(false);
    }
  };

  const performDeleteScript = async (scriptId: number) => {
    try {
      const response = await scriptAPI.deleteScript(scriptId);
      if (response.success) {
        setScripts((prev) => prev.filter((script) => script.id !== scriptId));
        showAlert({ message: "剧本删除成功", variant: "success" });
      } else {
        showAlert({
          message: `删除失败：${response.error || "未知错误"}`,
          variant: "error",
        });
      }
    } catch (error) {
      console.error("删除剧本失败:", error);
      showAlert({ message: "删除剧本失败", variant: "error" });
    }
  };

  const performRegenerateScript = async (scriptId: number) => {
    try {
      const response = await scriptAPI.regenerateScript(scriptId);
      if (response.success && response.data) {
        setScripts((prev) =>
          prev.map((script) =>
            script.id === scriptId ? (response.data as Script) : script,
          ),
        );
        showAlert({ message: "剧本重新生成成功", variant: "success" });
      } else {
        showAlert({
          message: `重新生成失败：${response.error || "未知错误"}`,
          variant: "error",
        });
      }
    } catch (error) {
      console.error("重新生成剧本失败:", error);
      showAlert({ message: "重新生成剧本失败", variant: "error" });
    }
  };

  const handleDeleteScript = (scriptId: number) => {
    showAlert({
      title: "确认删除剧本",
      message: "确定要删除这个剧本吗？",
      variant: "warning",
      confirmText: "删除",
      onConfirm: () => {
        void performDeleteScript(scriptId);
      },
    });
  };

  const handleRegenerateScript = (scriptId: number) => {
    showAlert({
      title: "确认重新生成",
      message: "确定要重新生成这个剧本吗？",
      variant: "warning",
      confirmText: "重新生成",
      onConfirm: () => {
        void performRegenerateScript(scriptId);
      },
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (!episode) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">剧集不存在</h2>
          <button
            onClick={() => router.push("/stories")}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            返回故事列表
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {episode && (
          <div className="mb-3 text-xs text-gray-500">
            scene_count: {getSceneCount(episode) || "—"}
          </div>
        )}
        {/* 头部 */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                第{episode.episode_number}集: {episode.title}
              </h1>
              <p className="mt-2 text-gray-600">
                {episode.duration_minutes}分钟 •{" "}
                {getSceneCount(episode) || "未知"}个场景
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => router.push(`/stories/${episode.story_id}`)}
                className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
              >
                返回故事
              </button>
              <button
                onClick={() => router.push(`/episodes/${episodeId}/storyboard`)}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
              >
                分镜管理
              </button>
              <button
                onClick={() => setShowGenerateForm(true)}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
              >
                生成剧本
              </button>
            </div>
          </div>
        </div>

        {/* 剧集信息 */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">剧集详情</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">剧集概要</h3>
              <p className="text-gray-600 mb-4">
                {episode.summary || "暂无概要"}
              </p>

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
                  Object.entries(episode.character_arcs).map(
                    ([character, arc]) => (
                      <div key={character} className="mb-2">
                        <span className="font-medium">{character}:</span>{" "}
                        {String(arc)}
                      </div>
                    ),
                  )
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
                      (typeof conflict === "string"
                        ? conflict
                        : `冲突 ${idx + 1}`);
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
                          <span className="font-medium text-red-900">
                            {description}
                          </span>
                          {intensity && (
                            <span
                              className={`text-xs px-2 py-0.5 rounded ${intensityClass}`}
                            >
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
          {/* 场景列表（来自 AI 生成数据） */}
          <div className="mt-6">
            <h3 className="font-medium text-gray-900 mb-2">场景列表</h3>
            {extractScenes(episode).length === 0 ? (
              <p className="text-gray-500 text-sm">
                暂无场景数据（可重新生成剧集后刷新）。
              </p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {extractScenes(episode).map(
                  (scene: Record<string, unknown>, idx: number) => {
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
                      (scene as { scene_number?: number | string }).scene_number ??
                      idx + 1;
                    return (
                      <div key={idx} className="border rounded p-3 bg-gray-50">
                        <div className="flex items-center justify-between">
                          <div className="font-medium text-gray-900">
                            场景 {sceneNumber}
                          </div>
                          {status && (
                            <span className="text-xs text-gray-600">
                              {status}
                            </span>
                          )}
                        </div>
                        <div className="text-sm text-gray-800 mt-1">
                          {title}
                        </div>
                        {desc && (
                          <div className="text-xs text-gray-600 mt-1 line-clamp-3">
                            {desc}
                          </div>
                        )}
                        {(loc || tod) && (
                          <div className="text-xs text-gray-500 mt-2">
                            {loc ? `地点：${loc}` : ""}{" "}
                            {tod ? ` · 时间：${tod}` : ""}
                          </div>
                        )}
                      </div>
                    );
                  },
                )}
              </div>
            )}
          </div>
        </div>

        {/* 剧本生成表单 */}
        {showGenerateForm && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4">📝 生成剧本</h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  剧本格式
                </label>
                <select
                  value={generateForm.format_type}
                  onChange={(e) =>
                    setGenerateForm((prev) => ({
                      ...prev,
                      format_type: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {formats.map((format) => (
                    <option key={format.value} value={format.value}>
                      {format.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  语言
                </label>
                <select
                  value={generateForm.language}
                  onChange={(e) =>
                    setGenerateForm((prev) => ({
                      ...prev,
                      language: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {languages.map((language) => (
                    <option key={language.value} value={language.value}>
                      {language.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  对话风格
                </label>
                <select
                  value={generateForm.dialogue_style}
                  onChange={(e) =>
                    setGenerateForm((prev) => ({
                      ...prev,
                      dialogue_style: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="formal">正式</option>
                  <option value="natural">自然</option>
                  <option value="casual">随意</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  场景描述详细程度
                </label>
                <select
                  value={generateForm.scene_detail_level}
                  onChange={(e) =>
                    setGenerateForm((prev) => ({
                      ...prev,
                      scene_detail_level: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="minimal">简洁</option>
                  <option value="medium">中等</option>
                  <option value="detailed">详细</option>
                </select>
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                额外要求
              </label>
              <textarea
                value={generateForm.additional_requirements}
                onChange={(e) =>
                  setGenerateForm((prev) => ({
                    ...prev,
                    additional_requirements: e.target.value,
                  }))
                }
                placeholder="对剧本生成的特殊要求"
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* 模型与温度 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-2">
              <MultiModelSelector
                label="模型"
                value={generateForm.model ? [generateForm.model] : []}
                onChange={(ids) =>
                  setGenerateForm((prev) => ({ ...prev, model: ids[0] || "" }))
                }
                modelType="text"
                multiple={false}
                helperText="留空将使用后端推荐模型"
                className="md:col-span-1"
              />
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  温度（{(generateForm.temperature ?? 0.7).toFixed(1)}）
                </label>
                <input
                  type="range"
                  min={0}
                  max={1.5}
                  step={0.1}
                  value={generateForm.temperature ?? 0.7}
                  onChange={(e) =>
                    setGenerateForm((prev) => ({
                      ...prev,
                      temperature: parseFloat(e.target.value),
                    }))
                  }
                  className="w-full"
                />
              </div>
              <div className="flex items-end">
                <label className="text-sm text-gray-700 flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={useAsync}
                    onChange={(e) => setUseAsync(e.target.checked)}
                  />{" "}
                  异步任务
                </label>
              </div>
            </div>

            {/* 提示词预览 */}
            <div className="mb-2">
              <button
                type="button"
                onClick={async () => {
                  setPromptPreview("加载中...");
                  const res = await scriptAPI.previewScriptPrompt(generateForm);
                  if (res.success && res.data)
                    setPromptPreview(res.data.prompt ?? "（空内容）");
                  else setPromptPreview("生成提示词失败");
                }}
                className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
              >
                提示词预览
              </button>
            </div>
            {promptPreview && (
              <div className="mt-2 bg-gray-50 p-3 rounded text-sm whitespace-pre-wrap">
                {promptPreview}
              </div>
            )}

            <div className="flex gap-2">
              <button
                onClick={handleGenerateScript}
                disabled={generating}
                className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {generating ? "生成中..." : "开始生成"}
              </button>
              <button
                onClick={() => setShowGenerateForm(false)}
                className="bg-gray-500 text-white px-6 py-2 rounded-lg hover:bg-gray-600"
              >
                取消
              </button>
            </div>
          </div>
        )}

        {/* 剧本列表 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">剧本列表</h2>
            <span className="text-sm text-gray-500">
              共 {scripts.length} 个剧本
            </span>
          </div>

          {scripts.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-gray-400 text-4xl mb-4">📝</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                暂无剧本
              </h3>
              <p className="text-gray-600 mb-4">开始生成您的第一个剧本吧！</p>
              <button
                onClick={() => setShowGenerateForm(true)}
                className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
              >
                生成剧本
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {scripts.map((script) => (
                <div
                  key={script.id}
                  className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-medium text-gray-900">
                          {script.title}
                        </h3>
                        <span className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded-full">
                          {formats.find((f) => f.value === script.format_type)
                            ?.label || script.format_type}
                        </span>
                        <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                          {languages.find((l) => l.value === script.language)
                            ?.label || script.language}
                        </span>
                        <span
                          className={`px-2 py-1 text-xs rounded-full ${
                            script.status === "published"
                              ? "bg-green-100 text-green-800"
                              : script.status === "approved"
                              ? "bg-blue-100 text-blue-800"
                              : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {script.status === "published"
                            ? "已发布"
                            : script.status === "approved"
                            ? "已批准"
                            : "草稿"}
                        </span>
                      </div>

                      <div className="flex items-center gap-4 text-xs text-gray-500 mb-2">
                        <span>字数: {script.word_count || 0}</span>
                        <span>字符: {script.character_count || 0}</span>
                        <span>页数: {script.page_count || 0}</span>
                        <span>版本: {script.version}</span>
                      </div>

                      <div className="text-xs text-gray-500">
                        创建: {new Date(script.created_at).toLocaleDateString()}
                      </div>
                    </div>

                    <div className="flex gap-2 ml-4">
                      <button
                        onClick={() => router.push(`/scripts/${script.id}`)}
                        className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                      >
                        查看内容
                      </button>
                      <button
                        onClick={() => handleRegenerateScript(script.id)}
                        className="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700"
                      >
                        重新生成
                      </button>
                      <button
                        onClick={() => handleDeleteScript(script.id)}
                        className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                      >
                        删除
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
