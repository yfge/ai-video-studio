"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  EpisodeWorkspaceHeader,
  WorkspaceOverviewTabContent,
  WorkspaceScriptTabContent,
  WorkspaceTimelineTabContent,
  WorkspaceStoryboardTabContent,
  type WorkflowStatus,
} from "@/components/features/episode";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import { useEpisodeDetail } from "@/hooks/useEpisodeDetail";
import { scriptAPI } from "@/utils/api";

type TabKey = "overview" | "script" | "timeline" | "storyboard";

export default function EpisodeWorkspacePage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const episodeKey = params?.id?.toString() || "";
  const { showAlert } = useAlertModal();

  // Get initial tab from URL or default to "overview"
  const initialTab = (searchParams.get("tab") as TabKey) || "overview";
  const [activeTab, setActiveTab] = useState<TabKey>(initialTab);

  // Get initial scriptId from URL
  const urlScriptId = searchParams.get("scriptId");
  const initialScriptId = urlScriptId ? Number(urlScriptId) : null;

  // Use the full episode detail hook for all state
  const state = useEpisodeDetail({ episodeKey, showAlert });
  const {
    episode,
    scripts,
    loading,
    selectedScript,
    selectedScriptId,
    setSelectedScriptId,
    normalizedScenes,
    normalizedScenesLoading,
    normalizedScenesError,
    selectedAudioTimeline,
    selectedStoryboard,
    timingModel,
    setTimingModel,
    // Script generation state
    formats,
    languages,
    generating,
    setGenerating,
    useAsync,
    setUseAsync,
    promptPreview,
    setPromptPreview,
    generateForm,
    setGenerateForm,
    setScripts,
  } = state;

  // Sync URL scriptId to hook state when scripts are loaded
  useEffect(() => {
    if (!scripts || scripts.length === 0) return;
    if (initialScriptId && scripts.some((s) => s.id === initialScriptId)) {
      // URL has a valid scriptId, sync to hook
      if (selectedScriptId !== initialScriptId) {
        setSelectedScriptId(initialScriptId);
      }
    }
  }, [scripts, initialScriptId, selectedScriptId, setSelectedScriptId]);

  // Get the first/main script
  const mainScript = selectedScript ?? scripts?.[0] ?? null;

  // Calculate workflow status based on data
  const workflowStatus: WorkflowStatus = useMemo(() => {
    const hasScript = scripts && scripts.length > 0;
    const hasTimeline = Boolean(selectedAudioTimeline);
    const hasStoryboard = Boolean(selectedStoryboard);

    return {
      script: hasScript ? "ready" : "pending",
      timeline: hasTimeline ? "ready" : "pending",
      storyboard: hasStoryboard ? "ready" : "pending",
    };
  }, [scripts, selectedAudioTimeline, selectedStoryboard]);

  // Build URL with tab and scriptId params
  const buildUrl = useCallback(
    (tab: TabKey, scriptId: number | null) => {
      const params = new URLSearchParams();
      params.set("tab", tab);
      if (scriptId) {
        params.set("scriptId", String(scriptId));
      }
      return `/episodes/${episodeKey}/workspace?${params.toString()}`;
    },
    [episodeKey]
  );

  // Update URL when tab changes
  const handleTabChange = useCallback(
    (tab: TabKey) => {
      setActiveTab(tab);
      router.replace(buildUrl(tab, selectedScriptId), {
        scroll: false,
      });
    },
    [router, buildUrl, selectedScriptId]
  );

  // Handle script selection change - update both state and URL
  const handleScriptChange = useCallback(
    (scriptId: number | null) => {
      setSelectedScriptId(scriptId);
      router.replace(buildUrl(activeTab, scriptId), {
        scroll: false,
      });
    },
    [setSelectedScriptId, router, buildUrl, activeTab]
  );

  // Navigation handlers
  const handleNavigateBack = useCallback(() => {
    const storyId = episode?.story_id;
    if (storyId) {
      router.push(`/stories/${storyId}`);
    } else {
      router.push("/stories");
    }
  }, [router, episode]);

  // Handle script generation directly in workspace
  const handleGenerateScript = useCallback(async () => {
    if (!episode?.id) {
      showAlert({ message: "剧集数据未加载", variant: "warning" });
      return;
    }
    try {
      setGenerating(true);
      const payload = {
        ...generateForm,
        episode_id: episode.id,
      };
      if (useAsync) {
        const res = await scriptAPI.generateScriptAsync(payload);
        if (res.success && res.data) {
          showAlert({
            message: `剧本生成任务已创建（task_id=${res.data.task_id}）`,
            variant: "info",
          });
        } else {
          showAlert({
            message: `创建剧本生成任务失败：${res.error || "未知错误"}`,
            variant: "error",
          });
        }
      } else {
        const res = await scriptAPI.generateScript(payload);
        if (res.success && res.data) {
          // Add the new script to the list
          setScripts((prev) => [res.data!, ...(prev || [])]);
          showAlert({ message: "剧本生成成功", variant: "success" });
        } else {
          showAlert({
            message: `剧本生成失败：${res.error || "未知错误"}`,
            variant: "error",
          });
        }
      }
    } catch (error) {
      console.error("Failed to generate script:", error);
      showAlert({ message: "剧本生成失败", variant: "error" });
    } finally {
      setGenerating(false);
    }
  }, [episode?.id, generateForm, useAsync, setGenerating, setScripts, showAlert]);

  const handleGenerateTimeline = useCallback(() => {
    setActiveTab("timeline");
    router.replace(buildUrl("timeline", selectedScriptId), { scroll: false });
  }, [router, buildUrl, selectedScriptId]);

  const handleGenerateStoryboard = useCallback(() => {
    // Navigate to storyboard page
    router.push(`/episodes/${episodeKey}/storyboard`);
  }, [router, episodeKey]);

  // State for script regeneration
  const [regenerating, setRegenerating] = useState(false);

  // Handle script regeneration with optional model override
  const handleRegenerateScript = useCallback(async (model?: string) => {
    if (!mainScript?.id) {
      showAlert({ message: "没有可重新生成的剧本", variant: "warning" });
      return;
    }
    try {
      setRegenerating(true);
      const res = await scriptAPI.regenerateScript(
        mainScript.id,
        model ? { model } : undefined
      );
      if (res.success && res.data) {
        // Update the script in the list
        setScripts((prev) =>
          prev?.map((s) => (s.id === mainScript.id ? res.data! : s)) || []
        );
        showAlert({ message: "剧本重新生成成功", variant: "success" });
      } else {
        showAlert({
          message: `剧本重新生成失败：${res.error || "未知错误"}`,
          variant: "error",
        });
      }
    } catch (error) {
      console.error("Failed to regenerate script:", error);
      showAlert({ message: "剧本重新生成失败", variant: "error" });
    } finally {
      setRegenerating(false);
    }
  }, [mainScript?.id, setScripts, showAlert]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  if (!loading && !episode) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-red-500">剧集不存在</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <EpisodeWorkspaceHeader
          episode={episode!}
          script={mainScript}
          workflowStatus={workflowStatus}
          activeTab={activeTab}
          onTabChange={handleTabChange}
          onNavigateBack={handleNavigateBack}
          onGenerateScript={handleGenerateScript}
          onGenerateTimeline={handleGenerateTimeline}
          onGenerateStoryboard={handleGenerateStoryboard}
        />

        {/* Script Selector - Page Level */}
        {scripts && scripts.length > 0 && (
          <div className="mt-4 bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium text-gray-700 whitespace-nowrap">
                当前剧本
              </label>
              <select
                value={selectedScriptId ?? ""}
                onChange={(e) => {
                  const next = Number(e.target.value);
                  handleScriptChange(Number.isFinite(next) ? next : null);
                }}
                className="flex-1 max-w-md px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              >
                <option value="" disabled>
                  请选择剧本
                </option>
                {scripts.map((script) => {
                  // Avoid duplicate version display if title already contains version
                  const hasVersionInTitle = /\(v[\d.]+\)$/.test(script.title || "");
                  const versionSuffix = script.version && !hasVersionInTitle ? ` (v${script.version})` : "";
                  return (
                    <option key={script.id} value={script.id}>
                      {script.title}{versionSuffix} - ID: {script.id}
                    </option>
                  );
                })}
              </select>
              <span className="text-xs text-gray-500">
                共 {scripts.length} 个剧本
              </span>
            </div>
          </div>
        )}

        {/* Tab Content */}
        <div className="mt-6">
          {activeTab === "overview" && episode && (
            <WorkspaceOverviewTabContent episode={episode} />
          )}
          {activeTab === "script" && (
            <WorkspaceScriptTabContent
              script={mainScript}
              generateForm={generateForm}
              setGenerateForm={setGenerateForm}
              formats={formats}
              languages={languages}
              useAsync={useAsync}
              setUseAsync={setUseAsync}
              promptPreview={promptPreview}
              setPromptPreview={setPromptPreview}
              generating={generating}
              onGenerate={handleGenerateScript}
              onRegenerateScript={mainScript ? handleRegenerateScript : undefined}
              regenerating={regenerating}
            />
          )}
          {activeTab === "timeline" && episode && (
            <WorkspaceTimelineTabContent
              scripts={scripts}
              selectedScriptId={selectedScriptId}
              selectedScript={selectedScript}
              selectedAudioTimeline={selectedAudioTimeline}
              selectedStoryboard={selectedStoryboard}
              normalizedScenes={normalizedScenes}
              normalizedScenesLoading={normalizedScenesLoading}
              normalizedScenesError={normalizedScenesError}
              timingModel={timingModel}
              setTimingModel={setTimingModel}
              showAlert={showAlert}
            />
          )}
          {activeTab === "storyboard" && (
            <WorkspaceStoryboardTabContent
              episodeKey={episodeKey}
              scripts={scripts}
              selectedScriptId={selectedScriptId}
              selectedScript={selectedScript}
              onSelectScript={handleScriptChange}
              hasStoryboard={workflowStatus.storyboard === "ready"}
              showAlert={showAlert}
            />
          )}
        </div>
      </div>
    </div>
  );
}
