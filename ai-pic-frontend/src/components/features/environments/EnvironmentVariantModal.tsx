"use client";

import { useMemo, useState } from "react";

import { ImageToImageModal, useAlertModal } from "@/components/shared/modals";
import {
  AIModelType,
  storyStructureAPI,
  type Environment,
  type StyleSpec,
} from "@/utils/api";

import type { EnvironmentImage } from "./types";

interface EnvironmentVariantModalProps {
  envKey: string;
  target: EnvironmentImage | null;
  env: Environment;
  imageSrc: (url: string) => string;
  onClose: () => void;
}

export function EnvironmentVariantModal({
  envKey,
  target,
  env,
  imageSrc,
  onClose,
}: EnvironmentVariantModalProps) {
  const { showAlert } = useAlertModal();
  const [submitting, setSubmitting] = useState(false);
  const defaultPrompt = useMemo(
    () => env?.description || env?.name || "基于该环境参考图生成一致风格的变体",
    [env],
  );

  if (!target) return null;

  const handleSubmit = async (payload: {
    prompt: string;
    model?: string;
    generation_profile?: string;
    count: number;
    size?: string;
    aspect_ratio?: string;
    style?: string;
    style_preset_id?: string;
    style_spec?: StyleSpec;
    referenceImages: string[];
  }) => {
    if (!envKey || !target) return;
    try {
      setSubmitting(true);
      const res = await storyStructureAPI.generateEnvironmentImageVariantsAsync(
        envKey,
        {
          base_image: target.url,
          prompt: payload.prompt,
          model: payload.model,
          generation_profile: payload.generation_profile,
          count: payload.count,
          size: payload.size,
          aspect_ratio: payload.aspect_ratio,
          style: payload.style,
          style_preset_id: payload.style_preset_id,
          style_spec: payload.style_spec,
          reference_images: payload.referenceImages,
        },
      );
      if (res.success) {
        showAlert({
          title: "已创建环境图变体任务",
          message: "任务将在后台生成，完成后刷新即可看到新图片。",
          variant: "success",
        });
        onClose();
      } else {
        showAlert({ message: res.error || "变体生成失败", variant: "error" });
      }
    } catch (error) {
      console.error(error);
      showAlert({ message: "变体生成失败", variant: "error" });
    } finally {
      setSubmitting(false);
    }
  };

  const referenceImage = imageSrc(target.url);

  return (
    <ImageToImageModal
      open={!!target}
      onClose={onClose}
      title="环境图生图"
      description="参考当前环境图，调整模型与参数后提交生成变体。"
      referenceSections={[{ title: "参考图", images: [referenceImage] }]}
      defaultSelected={[referenceImage]}
      defaultPrompt={defaultPrompt}
      defaultCount={1}
      modelType={AIModelType.ImageToImage}
      modelCacheKey="environment-img2img"
      submitting={submitting}
      onSubmit={handleSubmit}
    />
  );
}
