"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  OperatorPanel,
  OperatorShell,
  operatorButtonClass,
} from "@/components/shared";
import { useStories, type UseStoriesOptions } from "@/hooks/useStories";
import type { SingleVideoProjectResponse } from "@/utils/api/types";
import { episodeWorkspaceHref } from "@/utils/routes";
import { SingleVideoProjectModal } from "./SingleVideoProjectModal";
import { StoryGenerateForm } from "./StoryGenerateForm";
import { StoryListSection } from "./StoryListSection";

export function StoryProductionBoard({
  showAlert,
}: {
  showAlert: UseStoriesOptions["showAlert"];
}) {
  const router = useRouter();
  const [showSingleVideoForm, setShowSingleVideoForm] = useState(false);
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
  const openSingleVideoProject = (project: SingleVideoProjectResponse) => {
    router.push(
      episodeWorkspaceHref(project.episode_id, {
        tab: "script",
        extraParams: project.task_id ? { taskId: project.task_id } : undefined,
      }),
    );
  };

  return (
    <OperatorShell
      title="视频项目"
      subtitle="单条视频可直接创建；系列内容继续按故事和剧集组织"
      breadcrumb={["IP 中心", "视频生产"]}
    >
      <div className="space-y-5">
        <OperatorPanel className="p-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <h2 className="text-sm font-semibold text-gray-950">故事入口</h2>
              <p className="mt-1 text-xs text-gray-500">
                3–5 分钟视频可跳过故事与剧集配置；系列项目继续使用完整生产结构。
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setShowSingleVideoForm(true)}
                className={operatorButtonClass("primary")}
              >
                创建单条视频
              </button>
              <button
                type="button"
                onClick={openGenerateForm}
                className={operatorButtonClass("secondary")}
              >
                创建系列故事
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
          onOpenSingleVideoForm={() => setShowSingleVideoForm(true)}
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
      <SingleVideoProjectModal
        open={showSingleVideoForm}
        onClose={() => setShowSingleVideoForm(false)}
        onCreated={openSingleVideoProject}
      />
    </OperatorShell>
  );
}
