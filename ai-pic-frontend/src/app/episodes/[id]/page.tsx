"use client";

import { useParams, useRouter } from "next/navigation";
import { scriptAPI } from "@/utils/api";
import type { Script } from "@/utils/api";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import {
  EpisodeHeader,
  EpisodeDetails,
  AudioTimelineSection,
  ScriptGenerationForm,
  ScriptList,
} from "@/components/features";
import { useEpisodeDetail } from "@/hooks/useEpisodeDetail";

export default function EpisodeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const episodeKey = params?.id?.toString() || "";
  const { showAlert } = useAlertModal();

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
    episodeMeta,
    selectedAudioTimeline,
    selectedStoryboard,
    formats,
    languages,
    generating,
    setGenerating,
    showGenerateForm,
    setShowGenerateForm,
    useAsync,
    setUseAsync,
    promptPreview,
    setPromptPreview,
    generateForm,
    setGenerateForm,
    overwriteSceneAudio,
    setOverwriteSceneAudio,
    overwriteTimeline,
    setOverwriteTimeline,
    overwriteStoryboard,
    setOverwriteStoryboard,
    minPauseSeconds,
    setMinPauseSeconds,
    timingModel,
    setTimingModel,
    useDurationControl,
    setUseDurationControl,
    sceneAudioBusy,
    setSceneAudioBusy,
    timelineBusy,
    setTimelineBusy,
    storyboardBusy,
    setStoryboardBusy,
    sceneAudioTaskId,
    setSceneAudioTaskId,
    timelineTaskId,
    setTimelineTaskId,
    storyboardTaskId,
    setStoryboardTaskId,
    sceneAudioTask,
    timelineTask,
    storyboardTask,
    setScripts,
  } = state;

  const handleGenerateScript = async () => {
    try {
      setGenerating(true);
      if (useAsync) {
        const response = await scriptAPI.generateScriptAsync(generateForm);
        if (response.success) {
          showAlert({ message: "已创建任务，请稍后在任务页查看进度", variant: "info" });
        } else {
          showAlert({ message: `剧本生成失败：${response.error || "未知错误"}`, variant: "error" });
        }
      } else {
        const response = await scriptAPI.generateScript(generateForm);
        if (response.success && response.data) {
          setScripts((prev) => [response.data as Script, ...prev]);
          setShowGenerateForm(false);
          showAlert({ message: "剧本生成成功！", variant: "success" });
        } else {
          showAlert({ message: `剧本生成失败：${response.error || "未知错误"}`, variant: "error" });
        }
      }
    } catch (error) {
      console.error("剧本生成失败:", error);
      showAlert({ message: "剧本生成失败", variant: "error" });
    } finally {
      setGenerating(false);
    }
  };

  const handleGenerateSceneDialogueAudio = async () => {
    if (!selectedScriptId) {
      showAlert({ message: "请先选择一个剧本", variant: "warning" });
      return;
    }
    try {
      setSceneAudioBusy(true);
      const res = await scriptAPI.generateSceneDialogueAudioAsync(selectedScriptId, {
        overwrite_audio: overwriteSceneAudio,
        overwrite_beats: true,
        timing_model: timingModel || undefined,
      });
      if (res.success && res.data) {
        setSceneAudioTaskId(res.data.task_id);
        showAlert({ message: `对白音轨任务已创建（task_id=${res.data.task_id}）`, variant: "info" });
      } else {
        showAlert({ message: `创建对白音轨任务失败：${res.error || "未知错误"}`, variant: "error" });
      }
    } catch (error) {
      console.error("创建对白音轨任务失败:", error);
      showAlert({ message: "创建对白音轨任务失败", variant: "error" });
    } finally {
      setSceneAudioBusy(false);
    }
  };

  const handleGenerateAudioTimeline = async () => {
    if (!selectedScriptId) {
      showAlert({ message: "请先选择一个剧本", variant: "warning" });
      return;
    }
    try {
      setTimelineBusy(true);
      const res = await scriptAPI.generateAudioTimelineAsync(selectedScriptId, { overwrite: overwriteTimeline });
      if (res.success && res.data) {
        setTimelineTaskId(res.data.task_id);
        showAlert({ message: `时间轴任务已创建（task_id=${res.data.task_id}）`, variant: "info" });
      } else {
        showAlert({ message: `创建时间轴任务失败：${res.error || "未知错误"}`, variant: "error" });
      }
    } catch (error) {
      console.error("创建时间轴任务失败:", error);
      showAlert({ message: "创建时间轴任务失败", variant: "error" });
    } finally {
      setTimelineBusy(false);
    }
  };

  const handleGenerateStoryboardFromAudioTimeline = async () => {
    if (!selectedScriptId) {
      showAlert({ message: "请先选择一个剧本", variant: "warning" });
      return;
    }
    try {
      setStoryboardBusy(true);
      const res = await scriptAPI.generateStoryboardFromAudioTimelineAsync(selectedScriptId, {
        overwrite_existing: overwriteStoryboard,
        min_pause_seconds: minPauseSeconds,
      });
      if (res.success && res.data) {
        setStoryboardTaskId(res.data.task_id);
        showAlert({ message: `分镜占位任务已创建（task_id=${res.data.task_id}）`, variant: "info" });
      } else {
        showAlert({ message: `创建分镜占位任务失败：${res.error || "未知错误"}`, variant: "error" });
      }
    } catch (error) {
      console.error("创建分镜占位任务失败:", error);
      showAlert({ message: "创建分镜占位任务失败", variant: "error" });
    } finally {
      setStoryboardBusy(false);
    }
  };

  const handleDeleteScript = (scriptId: number) => {
    showAlert({
      title: "确认删除剧本",
      message: "确定要删除这个剧本吗？",
      variant: "warning",
      confirmText: "删除",
      onConfirm: async () => {
        try {
          const response = await scriptAPI.deleteScript(scriptId);
          if (response.success) {
            setScripts((prev) => prev.filter((s) => s.id !== scriptId));
            showAlert({ message: "剧本删除成功", variant: "success" });
          } else {
            showAlert({ message: `删除失败：${response.error || "未知错误"}`, variant: "error" });
          }
        } catch (error) {
          console.error("删除剧本失败:", error);
          showAlert({ message: "删除剧本失败", variant: "error" });
        }
      },
    });
  };

  const handleRegenerateScript = (scriptId: number) => {
    showAlert({
      title: "确认重新生成",
      message: "确定要重新生成这个剧本吗？",
      variant: "warning",
      confirmText: "重新生成",
      onConfirm: async () => {
        try {
          const response = await scriptAPI.regenerateScript(scriptId);
          if (response.success && response.data) {
            setScripts((prev) => prev.map((s) => (s.id === scriptId ? (response.data as Script) : s)));
            showAlert({ message: "剧本重新生成成功", variant: "success" });
          } else {
            showAlert({ message: `重新生成失败：${response.error || "未知错误"}`, variant: "error" });
          }
        } catch (error) {
          console.error("重新生成剧本失败:", error);
          showAlert({ message: "重新生成剧本失败", variant: "error" });
        }
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
          <button onClick={() => router.push("/stories")} className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
            返回故事列表
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <EpisodeHeader
          episode={episode}
          onNavigateToStory={() =>
            router.push(`/stories/${episode.story_business_id || episode.story_id}`)
          }
          onNavigateToStoryboard={() => {
            const suffix = selectedScript?.id ? `?scriptId=${selectedScript.id}` : "";
            const id = episode?.business_id || episode?.id;
            router.push(`/episodes/${id}/storyboard${suffix}`);
          }}
          onShowGenerateForm={() => setShowGenerateForm(true)}
        />

        <AudioTimelineSection
          selectedScriptId={selectedScriptId}
          selectedScript={selectedScript}
          selectedAudioTimeline={selectedAudioTimeline}
          selectedStoryboard={selectedStoryboard}
          normalizedScenes={normalizedScenes}
          normalizedScenesLoading={normalizedScenesLoading}
          normalizedScenesError={normalizedScenesError}
          pipelineBusy={sceneAudioBusy || timelineBusy || storyboardBusy}
          timingModel={timingModel}
          setTimingModel={setTimingModel}
          useDurationControl={useDurationControl}
          setUseDurationControl={setUseDurationControl}
          onNavigateToTasks={() => router.push("/tasks")}
          onNavigateToScript={() => {
            if (selectedScript) {
              router.push(`/scripts/${selectedScript.business_id || selectedScript.id}`);
            }
          }}
        />

        <EpisodeDetails episode={episode} />

        {showGenerateForm && (
          <ScriptGenerationForm
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
            onCancel={() => setShowGenerateForm(false)}
          />
        )}

        <ScriptList
          scripts={scripts}
          formats={formats}
          languages={languages}
          onViewScript={(script) => router.push(`/scripts/${script.business_id || script.id}`)}
          onRegenerateScript={handleRegenerateScript}
          onDeleteScript={handleDeleteScript}
          onShowGenerateForm={() => setShowGenerateForm(true)}
        />
      </div>
    </div>
  );
}
