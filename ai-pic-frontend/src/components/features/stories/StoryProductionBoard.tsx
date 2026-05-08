"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  OperatorContextRail,
  OperatorListRow,
  OperatorMainCanvas,
  OperatorShell,
  OperatorState,
  OperatorWorkspace,
  StatusPill,
  operatorButtonClass,
} from "@/components/shared";
import { useStories, type UseStoriesOptions } from "@/hooks/useStories";
import type { Story } from "@/utils/api/types";
import { StoryGenerateForm } from "./StoryGenerateForm";
import { StoryProductionDetail } from "./StoryProductionDetail";
import { storyDisplayText } from "./StoryProductionModel";

export function StoryProductionBoard({
  showAlert,
}: {
  showAlert: UseStoriesOptions["showAlert"];
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
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
    handleGenerateStory,
    handleCharacterToggle,
    handlePreviewPrompt,
    openGenerateForm,
    closeGenerateForm,
    navigateToVirtualIP,
  } = state;

  const selectedStoryKey =
    searchParams.get("story") || stories[0]?.business_id || "";

  useEffect(() => {
    if (!searchParams.get("story") && stories[0]?.business_id) {
      const params = new URLSearchParams(searchParams.toString());
      params.set("story", stories[0].business_id);
      router.replace(`/stories?${params.toString()}`, { scroll: false });
    }
  }, [router, searchParams, stories]);

  const selectStory = (story: Story) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("story", story.business_id);
    router.replace(`/stories?${params.toString()}`, { scroll: false });
  };

  return (
    <OperatorShell
      title="IP 故事生产"
      subtitle="围绕 IP 组织故事、剧集和生成准备"
      breadcrumb={["IP 中心", "故事生产"]}
    >
      <OperatorWorkspace
        variant="rail-main"
        rail={
          <OperatorContextRail
            title="故事列表"
            subtitle="选择故事"
            action={
              <button
                type="button"
                onClick={openGenerateForm}
                className={operatorButtonClass("primary")}
              >
                从 IP 新建
              </button>
            }
          >
            {loading ? (
              <div className="p-1 text-sm text-gray-500">加载中...</div>
            ) : (
              <div className="space-y-2">
              {stories.map((story) => (
                <OperatorListRow
                  key={story.id}
                  onClick={() => selectStory(story)}
                  selected={selectedStoryKey === story.business_id}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium text-gray-950">
                        {story.title}
                      </div>
                      <div className="mt-1 text-xs text-gray-500">
                        {story.genre}
                        {story.theme ? ` · ${story.theme}` : ""}
                      </div>
                    </div>
                    <StatusPill tone={story.status === "published" ? "green" : "gray"}>
                      {story.status}
                    </StatusPill>
                  </div>
                  <p className="mt-2 line-clamp-2 text-xs text-gray-600">
                    {storyDisplayText(story.synopsis, story.premise)}
                  </p>
                </OperatorListRow>
              ))}
              </div>
            )}
          </OperatorContextRail>
        }
        main={
          <OperatorMainCanvas>
            {selectedStoryKey ? (
              <StoryProductionDetail storyKey={selectedStoryKey} />
            ) : (
              <OperatorState title="暂无故事，请先创建故事。" />
            )}
          </OperatorMainCanvas>
        }
      />

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
