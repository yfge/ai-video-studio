"use client";

import {
  OperatorPanel,
  OperatorShell,
  operatorButtonClass,
} from "@/components/shared";
import { useStories, type UseStoriesOptions } from "@/hooks/useStories";
import { StoryGenerateForm } from "./StoryGenerateForm";
import { StoryListSection } from "./StoryListSection";

export function StoryProductionBoard({
  showAlert,
}: {
  showAlert: UseStoriesOptions["showAlert"];
}) {
  const state = useStories({ showAlert });
  const {
    stories,
    virtualIPs,
    loading,
    generating,
    showGenerateForm,
    generateForm,
    setGenerateForm,
    promptPreview,
    showPromptPreview,
    useAsync,
    setUseAsync,
    selectedGenre,
    setSelectedGenre,
    selectedStatus,
    setSelectedStatus,
    handleGenerateStory,
    handleDeleteStory,
    handleCharacterToggle,
    handlePreviewPrompt,
    openGenerateForm,
    closeGenerateForm,
    navigateToVirtualIP,
  } = state;

  return (
    <OperatorShell
      title="IP 故事生产"
      subtitle="围绕 IP 组织故事、剧集和生成准备"
      breadcrumb={["IP 中心", "故事生产"]}
    >
      <div className="space-y-5">
        <OperatorPanel className="p-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <h2 className="text-sm font-semibold text-gray-950">故事入口</h2>
              <p className="mt-1 text-xs text-gray-500">
                故事用于承接 IP
                角色、环境资产和剧集生产；详情页内继续处理就绪检查与剧集生成。
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={openGenerateForm}
                className={operatorButtonClass("primary")}
              >
                从 IP 新建
              </button>
            </div>
          </div>
        </OperatorPanel>

        <StoryListSection
          stories={stories}
          loading={loading}
          selectedGenre={selectedGenre}
          onSelectedGenreChange={setSelectedGenre}
          selectedStatus={selectedStatus}
          onSelectedStatusChange={setSelectedStatus}
          onOpenGenerateForm={openGenerateForm}
          onDelete={handleDeleteStory}
        />
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
    </OperatorShell>
  );
}
