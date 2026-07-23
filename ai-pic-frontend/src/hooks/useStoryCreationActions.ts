"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { storyAPI } from "@/utils/api/endpoints";
import type { Story, VirtualIP } from "@/utils/api/types";
import type { StoryGenerationForm } from "@/utils/storyOptions";

interface AlertOptions {
  title?: string;
  message: string;
  variant: "success" | "error" | "warning" | "info";
  confirmText?: string;
  onConfirm?: () => void;
}

interface StoryCreationActionsOptions {
  generateForm: StoryGenerationForm;
  useAsync: boolean;
  virtualIPs: VirtualIP[];
  showAlert: (options: AlertOptions) => void;
  onStoryCreated: (story: Story) => void;
  onClose: () => void;
}

function isInvalid(form: StoryGenerationForm): boolean {
  return (
    !form.title ||
    !form.additional_requirements?.trim() ||
    form.character_ids.length === 0
  );
}

export function useStoryCreationActions({
  generateForm,
  useAsync,
  virtualIPs,
  showAlert,
  onStoryCreated,
  onClose,
}: StoryCreationActionsOptions) {
  const router = useRouter();
  const [generating, setGenerating] = useState(false);

  const validate = () => {
    if (!isInvalid(generateForm)) return true;
    showAlert({
      message: "请填写标题、创作 Brief，并选择至少一个角色",
      variant: "warning",
    });
    return false;
  };

  const handleGenerateStory = async () => {
    if (!validate()) return;
    try {
      setGenerating(true);
      const response = useAsync
        ? await storyAPI.generateStoryAsync(generateForm)
        : await storyAPI.generateStory(generateForm);
      if (!response.success) {
        throw new Error(response.error || "未知错误");
      }
      if (useAsync) {
        const taskId = (response.data as { task_id?: number } | null)?.task_id;
        showAlert({
          message: taskId
            ? `已创建异步任务（ID: ${taskId}），可前往任务页查看进度`
            : "已创建异步任务，可前往任务页查看进度",
          variant: "info",
          confirmText: "去任务页",
          onConfirm: () => router.push("/tasks"),
        });
      } else if (response.data) {
        onStoryCreated(response.data as Story);
        showAlert({ message: "Story Seed 生成成功", variant: "success" });
      }
      onClose();
    } catch (error) {
      console.error("Story Seed 生成失败:", error);
      showAlert({
        message: `Story Seed 生成失败：${String(error)}`,
        variant: "error",
      });
    } finally {
      setGenerating(false);
    }
  };

  const handleSaveStorySeed = async () => {
    if (!validate()) return;
    const selected = virtualIPs.filter((item) =>
      generateForm.character_ids.includes(item.id),
    );
    const brief = generateForm.additional_requirements?.trim() || "";
    try {
      setGenerating(true);
      const response = await storyAPI.createStory({
        title: generateForm.title,
        story_format: generateForm.story_format,
        genre: generateForm.genre,
        workflow_mode: "novel_adaptation_v1",
        target_audience: generateForm.target_audience,
        premise: brief,
        synopsis: brief,
        main_conflict: brief,
        setting_time: generateForm.setting_time,
        setting_location: generateForm.setting_location,
        world_building: generateForm.world_building,
        story_seed_status: "draft",
        story_seed: {
          schema: "story_seed_v1",
          title: generateForm.title,
          premise: brief,
          outline: brief,
          protagonists: selected.map((item) => ({
            virtual_ip_business_id: item.business_id,
            initial_state:
              item.description || item.background_story || "沿用基础角色设定",
          })),
          world_constraints: generateForm.world_building
            ? [generateForm.world_building]
            : [],
          central_conflict: brief,
          ending_direction: null,
          target_audience: generateForm.target_audience || null,
          content_constraints: generateForm.content_restrictions || [],
        },
        characters: selected.map((item, index) => ({
          virtual_ip_id: item.id,
          character_name: item.name,
          role_type: index === 0 ? "protagonist" : "supporting",
          importance: index === 0 ? 5 : 3,
        })),
      });
      if (!response.success || !response.data) {
        throw new Error(response.error || "保存失败");
      }
      onStoryCreated(response.data as Story);
      onClose();
      showAlert({
        message: "Story Seed 草稿已本地保存；未调用模型",
        variant: "success",
      });
    } catch (error) {
      showAlert({
        message: `Story Seed 保存失败：${String(error)}`,
        variant: "error",
      });
    } finally {
      setGenerating(false);
    }
  };

  return { generating, handleGenerateStory, handleSaveStorySeed };
}
