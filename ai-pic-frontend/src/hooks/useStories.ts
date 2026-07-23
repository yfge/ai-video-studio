"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { storyAPI, virtualIPAPI } from "@/utils/api/endpoints";
import {
  STORY_GENERATE_DEFAULTS,
  STORY_GENRES,
  STORY_STATUSES,
  type StoryGenerationForm,
} from "@/utils/storyOptions";
import type { Story, VirtualIP } from "@/utils/api/types";
import { fetchAllPages } from "@/utils/api/pagination";
import { useStoryCreationActions } from "./useStoryCreationActions";

export interface UseStoriesOptions {
  showAlert: (options: {
    title?: string;
    message: string;
    variant: "success" | "error" | "warning" | "info";
    confirmText?: string;
    onConfirm?: () => void;
  }) => void;
}

export const GENRES = STORY_GENRES;
export const STATUSES = STORY_STATUSES;

const INITIAL_GENERATE_FORM: StoryGenerationForm = STORY_GENERATE_DEFAULTS;

export function useStories({ showAlert }: UseStoriesOptions) {
  const router = useRouter();

  const [allStories, setAllStories] = useState<Story[]>([]);
  const [virtualIPs, setVirtualIPs] = useState<VirtualIP[]>([]);
  const [loading, setLoading] = useState(true);
  const [showGenerateForm, setShowGenerateForm] = useState(false);

  const [selectedGenre, setSelectedGenre] = useState<string>("");
  const [selectedStatus, setSelectedStatus] = useState<string>("");
  const stories = useMemo(
    () =>
      allStories.filter(
        (story) =>
          (!selectedGenre || story.genre === selectedGenre) &&
          (!selectedStatus || story.status === selectedStatus),
      ),
    [allStories, selectedGenre, selectedStatus],
  );

  const [generateForm, setGenerateForm] = useState<StoryGenerationForm>(
    INITIAL_GENERATE_FORM,
  );
  const [promptPreview, setPromptPreview] = useState<string>("");
  const [showPromptPreview, setShowPromptPreview] = useState<boolean>(false);
  const [useAsync, setUseAsync] = useState<boolean>(true);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [storyItems, virtualIPItems] = await Promise.all([
        fetchAllPages((skip, limit) => storyAPI.getStories({ skip, limit })),
        fetchAllPages((skip, limit) =>
          virtualIPAPI.getVirtualIPs({ skip, limit }),
        ),
      ]);
      setAllStories(storyItems);
      setVirtualIPs(virtualIPItems);
    } catch (error) {
      console.error("加载数据失败:", error);
      showAlert({ message: "加载数据失败", variant: "error" });
    } finally {
      setLoading(false);
    }
  }, [showAlert]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const performDeleteStory = async (storyBusinessId: string) => {
    try {
      const response = await storyAPI.deleteStory(storyBusinessId);
      if (response.success) {
        setAllStories((prev) =>
          prev.filter((story) => story.business_id !== storyBusinessId),
        );
        showAlert({ message: "故事删除成功", variant: "success" });
      } else {
        showAlert({
          message: `删除失败：${response.error || "未知错误"}`,
          variant: "error",
        });
      }
    } catch (error) {
      console.error("删除故事失败:", error);
      showAlert({ message: "删除故事失败", variant: "error" });
    }
  };

  const handleDeleteStory = (storyBusinessId: string) => {
    showAlert({
      title: "确认删除",
      message: "确定要删除这个故事吗？",
      variant: "warning",
      confirmText: "删除",
      onConfirm: () => {
        void performDeleteStory(storyBusinessId);
      },
    });
  };

  const handleCharacterToggle = (characterId: number) => {
    setGenerateForm((prev) => ({
      ...prev,
      character_ids: prev.character_ids.includes(characterId)
        ? prev.character_ids.filter((id) => id !== characterId)
        : [...prev.character_ids, characterId],
    }));
  };

  const handlePreviewPrompt = async () => {
    try {
      if (
        !generateForm.title ||
        !generateForm.additional_requirements?.trim() ||
        generateForm.character_ids.length === 0
      ) {
        setShowPromptPreview(true);
        setPromptPreview("请填写标题、创作 Brief，并至少选择一个角色后再预览");
        return;
      }
      setShowPromptPreview(true);
      setPromptPreview("加载中...");
      const res = await storyAPI.previewStoryPrompt(generateForm);
      if (res.success && res.data) {
        setPromptPreview(res.data.prompt ?? "（空内容）");
      } else {
        setPromptPreview("生成提示词失败");
      }
    } catch {
      setPromptPreview("预览出错");
    }
  };

  const closeGenerateForm = () => {
    setShowGenerateForm(false);
    setGenerateForm(INITIAL_GENERATE_FORM);
    setPromptPreview("");
    setShowPromptPreview(false);
  };

  const { generating, handleGenerateStory, handleSaveStorySeed } =
    useStoryCreationActions({
      generateForm,
      useAsync,
      virtualIPs,
      showAlert,
      onStoryCreated: (story) =>
        setAllStories((current) => [story, ...current]),
      onClose: closeGenerateForm,
    });

  const openGenerateForm = () => setShowGenerateForm(true);

  const navigateToStory = (businessId: string) => {
    router.push(`/stories/${businessId}`);
  };

  const navigateToVirtualIP = () => {
    router.push("/virtual-ip");
  };

  return {
    // Core state
    stories,
    virtualIPs,
    loading,
    generating,
    showGenerateForm,

    // Filter state
    selectedGenre,
    setSelectedGenre,
    selectedStatus,
    setSelectedStatus,

    // Generate form state
    generateForm,
    setGenerateForm,
    promptPreview,
    showPromptPreview,
    useAsync,
    setUseAsync,

    // Event handlers
    handleGenerateStory,
    handleSaveStorySeed,
    handleDeleteStory,
    handleCharacterToggle,
    handlePreviewPrompt,
    openGenerateForm,
    closeGenerateForm,
    navigateToStory,
    navigateToVirtualIP,
  };
}
