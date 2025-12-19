"use client";

import { useParams, useRouter } from "next/navigation";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import {
  StoryDetailHeader,
  StorySummarySection,
  CharactersSection,
  AdditionalInfoSection,
  EpisodeGeneratePanel,
  EpisodeListSection,
} from "@/components/features";
import { useStoryDetail } from "@/hooks/useStoryDetail";

export default function StoryDetailPage() {
  const params = useParams();
  const router = useRouter();
  const storyKey = params?.id?.toString() || "";
  const { showAlert } = useAlertModal();

  const state = useStoryDetail({ storyKey, showAlert });

  const {
    story,
    episodes,
    scriptsByEpisode,
    loading,
    loadingScripts,
    genOpen,
    setGenOpen,
    genForm,
    setGenForm,
    promptPreview,
    useAsync,
    setUseAsync,
    vips,
    focusCharacters,
    handlePreviewPrompt,
    handleGenerateEpisodes,
    toggleFocusCharacter,
    navigateToStories,
    navigateToEpisode,
    navigateToStoryboard,
    navigateToScript,
  } = state;

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

  if (!story) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">故事不存在</h2>
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
        <StoryDetailHeader story={story} onBack={navigateToStories} />

        <StorySummarySection story={story} />

        <CharactersSection story={story} />

        <AdditionalInfoSection story={story} />

        <EpisodeGeneratePanel
          genOpen={genOpen}
          setGenOpen={setGenOpen}
          genForm={genForm}
          setGenForm={setGenForm}
          vips={vips}
          focusCharacters={focusCharacters}
          onToggleFocusCharacter={toggleFocusCharacter}
          useAsync={useAsync}
          setUseAsync={setUseAsync}
          promptPreview={promptPreview}
          onPreviewPrompt={handlePreviewPrompt}
          onGenerate={handleGenerateEpisodes}
        />

        <EpisodeListSection
          story={story}
          episodes={episodes}
          scriptsByEpisode={scriptsByEpisode}
          loadingScripts={loadingScripts}
          onNavigateToEpisode={navigateToEpisode}
          onNavigateToStoryboard={navigateToStoryboard}
          onNavigateToScript={navigateToScript}
        />
      </div>
    </div>
  );
}
