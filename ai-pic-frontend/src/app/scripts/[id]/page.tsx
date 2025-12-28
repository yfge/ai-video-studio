"use client";

import { useParams, useRouter } from "next/navigation";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import {
  ScriptHeader,
  WorkflowSteps,
  ScriptOverviewTab,
  ScriptScenesTab,
} from "@/components/features";
import { useScriptDetail, TABS } from "@/hooks/useScriptDetail";

export default function ScriptDetailPage() {
  const router = useRouter();
  const { id } = useParams();
  const scriptKey = (id as string) || "";
  const { showAlert } = useAlertModal();

  const state = useScriptDetail({ scriptKey, showAlert });

  const {
    activeTab,
    setActiveTab,
    script,
    setStructuredScenes,
    structureLoading,
    structureError,
    showStructureEditor,
    setShowStructureEditor,
    loading,
    showExportMenu,
    setShowExportMenu,
    focusedScene,
    setFocusedScene,
    scenes,
    dialogues,
    directions,
    activeScene,
    selectedNormalizedScene,
    sceneBeats,
    sceneShots,
    canEditStructure,
    handleExport,
    goToSceneDetails,
    goToSceneStructure,
  } = state;

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (!script) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100">
        <div className="text-center">
          <h2 className="mb-4 text-2xl font-bold text-gray-900">未找到剧本</h2>
          <button
            onClick={() => router.push("/stories")}
            className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
          >
            返回故事列表
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <div className="mx-auto max-w-7xl space-y-8 px-4 py-8 sm:px-6 lg:px-8">
        <ScriptHeader
          script={script}
          showExportMenu={showExportMenu}
          setShowExportMenu={setShowExportMenu}
          onExport={handleExport}
          onNavigateToEpisode={() =>
            router.push(
              `/episodes/${script.episode_business_id || script.episode_id}/workspace?tab=script&scriptId=${script.id}`,
            )
          }
          onNavigateToStoryboard={() =>
            router.push(`/episodes/${script.episode_business_id || script.episode_id}/storyboard`)
          }
        />

        <WorkflowSteps
          onGoToSceneDetails={goToSceneDetails}
          onGoToSceneStructure={goToSceneStructure}
          onGoToStoryboard={() =>
            router.push(`/episodes/${script.episode_business_id || script.episode_id}/storyboard`)
          }
        />

        <nav className="flex flex-wrap gap-2">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
                activeTab === tab.id
                  ? "border-blue-600 bg-blue-50 text-blue-700"
                  : "border-gray-200 bg-white text-gray-600 hover:border-blue-200"
              }`}
            >
              {tab.name}
            </button>
          ))}
        </nav>

        {activeTab === "overview" && (
          <ScriptOverviewTab
            script={script}
            scenes={scenes}
            dialogues={dialogues}
            directions={directions}
          />
        )}

        {activeTab === "scenes" && (
          <ScriptScenesTab
            script={script}
            scenes={scenes}
            dialogues={dialogues}
            directions={directions}
            focusedScene={focusedScene}
            setFocusedScene={setFocusedScene}
            activeScene={activeScene}
            selectedNormalizedScene={selectedNormalizedScene}
            sceneBeats={sceneBeats}
            sceneShots={sceneShots}
            structureLoading={structureLoading}
            structureError={structureError}
            showStructureEditor={showStructureEditor}
            setShowStructureEditor={setShowStructureEditor}
            canEditStructure={canEditStructure}
            setStructuredScenes={setStructuredScenes}
          />
        )}
      </div>
    </div>
  );
}
