"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { storyAPI, virtualIPAPI } from "@/utils/api/endpoints";
import {
  STORY_GENERATE_DEFAULTS,
  STORY_GENRES,
  STORY_STATUSES,
  type StoryGenerationForm,
} from "@/utils/storyOptions";
import type { Story, VirtualIP } from "@/utils/api/types";

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

  // Core state
  const [stories, setStories] = useState<Story[]>([]);
  const [virtualIPs, setVirtualIPs] = useState<VirtualIP[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [showGenerateForm, setShowGenerateForm] = useState(false);

  // Filter state
  const [selectedGenre, setSelectedGenre] = useState<string>("");
  const [selectedStatus, setSelectedStatus] = useState<string>("");

  // Generate form state
  const [generateForm, setGenerateForm] = useState<StoryGenerationForm>(
    INITIAL_GENERATE_FORM,
  );
  const [promptPreview, setPromptPreview] = useState<string>("");
  const [showPromptPreview, setShowPromptPreview] = useState<boolean>(false);
  const [useAsync, setUseAsync] = useState<boolean>(true);

  // Data loading
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [storiesResponse, virtualIPsResponse] = await Promise.all([
        storyAPI.getStories({
          genre: selectedGenre || undefined,
          status: selectedStatus || undefined,
          limit: 50,
        }),
        virtualIPAPI.getVirtualIPs(),
      ]);

      if (storiesResponse.success && storiesResponse.data) {
        setStories(storiesResponse.data);
      }
      if (virtualIPsResponse.success && virtualIPsResponse.data) {
        setVirtualIPs(virtualIPsResponse.data);
      }
    } catch (error) {
      console.error("加载数据失败:", error);
      showAlert({ message: "加载数据失败", variant: "error" });
    } finally {
      setLoading(false);
    }
  }, [selectedGenre, selectedStatus, showAlert]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  // Event handlers
  const handleGenerateStory = async () => {
    if (!generateForm.title || generateForm.character_ids.length === 0) {
      showAlert({
        message: "请填写标题并选择至少一个角色",
        variant: "warning",
      });
      return;
    }

    try {
      setGenerating(true);
      if (useAsync) {
        const response = await storyAPI.generateStoryAsync(generateForm);
        if (response.success) {
          const taskId = (response.data as { task_id?: number } | null)
            ?.task_id;
          showAlert({
            message: taskId
              ? `已创建异步任务（ID: ${taskId}），可前往任务页查看进度`
              : "已创建异步任务，可前往任务页查看进度",
            variant: "info",
            confirmText: "去任务页",
            onConfirm: () => {
              router.push("/tasks");
            },
          });
        } else {
          showAlert({
            message: `故事生成失败：${response.error || "未知错误"}`,
            variant: "error",
          });
        }
      } else {
        const response = await storyAPI.generateStory(generateForm);
        if (response.success && response.data) {
          setStories((prev) => [response.data as Story, ...prev]);
          showAlert({ message: "故事生成成功！", variant: "success" });
        } else {
          showAlert({
            message: `故事生成失败：${response.error || "未知错误"}`,
            variant: "error",
          });
        }
      }
      setShowGenerateForm(false);
      setGenerateForm(INITIAL_GENERATE_FORM);
      setPromptPreview("");
    } catch (error) {
      console.error("故事生成失败:", error);
      showAlert({ message: "故事生成失败", variant: "error" });
    } finally {
      setGenerating(false);
    }
  };

  const performDeleteStory = async (storyBusinessId: string) => {
    try {
      const response = await storyAPI.deleteStory(storyBusinessId);
      if (response.success) {
        setStories((prev) =>
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
      if (!generateForm.title || generateForm.character_ids.length === 0) {
        setShowPromptPreview(true);
        setPromptPreview("请填写标题并至少选择一个角色后再预览提示词");
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

  const openGenerateForm = () => setShowGenerateForm(true);

  const closeGenerateForm = () => {
    setShowGenerateForm(false);
    setGenerateForm(INITIAL_GENERATE_FORM);
    setPromptPreview("");
    setShowPromptPreview(false);
  };

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
    handleDeleteStory,
    handleCharacterToggle,
    handlePreviewPrompt,
    openGenerateForm,
    closeGenerateForm,
    navigateToStory,
    navigateToVirtualIP,
  };
}
