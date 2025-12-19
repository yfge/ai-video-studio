"use client";

import { Navigation } from "@/components/layouts";
import { AuthGuard } from "@/components/shared";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import {
  StoriesHeader,
  StoriesFilter,
  StoryCard,
  StoryGenerateForm,
} from "@/components/features";
import { useStories } from "@/hooks/useStories";

function StoriesPageContent() {
  const { showAlert } = useAlertModal();
  const state = useStories({ showAlert });

  const {
    stories,
    virtualIPs,
    loading,
    generating,
    showGenerateForm,
    selectedGenre,
    setSelectedGenre,
    selectedStatus,
    setSelectedStatus,
    generateForm,
    setGenerateForm,
    promptPreview,
    showPromptPreview,
    useAsync,
    setUseAsync,
    handleGenerateStory,
    handleDeleteStory,
    handleCharacterToggle,
    handlePreviewPrompt,
    openGenerateForm,
    closeGenerateForm,
    navigateToStory,
    navigateToVirtualIP,
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

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation title="故事管理" />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <StoriesHeader onGenerateClick={openGenerateForm} />

        <StoriesFilter
          selectedGenre={selectedGenre}
          setSelectedGenre={setSelectedGenre}
          selectedStatus={selectedStatus}
          setSelectedStatus={setSelectedStatus}
        />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {stories.map((story) => (
            <StoryCard
              key={story.id}
              story={story}
              onViewDetails={navigateToStory}
              onDelete={handleDeleteStory}
            />
          ))}
        </div>

        {stories.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">📚</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">暂无故事</h3>
            <p className="text-gray-600 mb-4">开始创作您的第一个故事吧！</p>
            <button
              onClick={openGenerateForm}
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
            >
              AI生成故事
            </button>
          </div>
        )}
      </div>

      <StoryGenerateForm
        open={showGenerateForm}
        onClose={closeGenerateForm}
        virtualIPs={virtualIPs}
        generateForm={generateForm}
        setGenerateForm={setGenerateForm}
        promptPreview={promptPreview}
        showPromptPreview={showPromptPreview}
        useAsync={useAsync}
        setUseAsync={setUseAsync}
        generating={generating}
        onCharacterToggle={handleCharacterToggle}
        onPreviewPrompt={handlePreviewPrompt}
        onSubmit={handleGenerateStory}
        onNavigateToVirtualIP={navigateToVirtualIP}
      />
    </div>
  );
}

export default function StoriesPage() {
  return (
    <AuthGuard>
      <StoriesPageContent />
    </AuthGuard>
  );
}
