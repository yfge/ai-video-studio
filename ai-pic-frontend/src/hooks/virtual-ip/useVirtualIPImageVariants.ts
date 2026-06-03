import { useMemo, useState } from "react";

import { virtualIPImageAPI } from "@/utils/api/endpoints";
import type { VirtualIPImage } from "@/utils/api/types";

import type { ImageGenerationFormState } from "./virtualIpImageTypes";
import { resolveImageUrl } from "./virtualIpImageConstants";

interface UseVirtualIPImageVariantsOptions {
  virtualIPId: number | null;
  generateForm: ImageGenerationFormState;
  recommendedModel: string;
  showAlert: (opts: {
    message: string;
    variant: "success" | "error" | "warning" | "info";
    title?: string;
    confirmText?: string;
    onConfirm?: () => void;
  }) => void;
  router: { push: (path: string) => void };
  onTaskCreated?: (taskId: number) => void;
}

export function useVirtualIPImageVariants({
  virtualIPId,
  generateForm,
  recommendedModel,
  showAlert,
  router,
  onTaskCreated,
}: UseVirtualIPImageVariantsOptions) {
  const [variantTarget, setVariantTarget] = useState<VirtualIPImage | null>(
    null,
  );
  const [variantPrompt, setVariantPrompt] = useState("");
  const [variantModalOpen, setVariantModalOpen] = useState(false);
  const [variantSubmitting, setVariantSubmitting] = useState(false);

  const handleOpenVariant = (image: VirtualIPImage) => {
    setVariantTarget(image);
    setVariantPrompt("为该角色生成不同角度/姿态，例如背面或全身照");
    setVariantModalOpen(true);
  };

  const variantReferenceSections = useMemo(() => {
    if (!variantTarget) return [];
    const url = resolveImageUrl(variantTarget);
    return url ? [{ title: "参考图", images: [url] }] : [];
  }, [variantTarget]);

  const handleSubmitVariant = async (payload: {
    prompt: string;
    model?: string;
    generation_profile?: string;
    count: number;
    size?: string;
    aspect_ratio?: string;
    seed?: number;
    steps?: number;
    cfg_scale?: number;
    negative_prompt?: string;
    strength?: number;
    image_reference?: string;
    image_fidelity?: number;
    human_fidelity?: number;
    style?: string;
    style_preset_id?: string;
    style_spec?: Record<string, unknown>;
    referenceImages: string[];
  }) => {
    if (!variantTarget || !virtualIPId) {
      showAlert({ message: "虚拟IP尚未加载", variant: "error" });
      return;
    }
    const modelFallback =
      payload.model ||
      (variantTarget.ai_model as string | undefined) ||
      generateForm.model ||
      recommendedModel ||
      "";

    try {
      setVariantSubmitting(true);
      const res = await virtualIPImageAPI.generateVariantAndSaveAsync(
        virtualIPId,
        variantTarget.id,
        {
          prompt: payload.prompt || variantPrompt,
          model: modelFallback || undefined,
          generation_profile:
            payload.generation_profile || generateForm.generation_profile,
          seed: payload.seed,
          steps: payload.steps,
          cfg_scale: payload.cfg_scale,
          negative_prompt: payload.negative_prompt,
          strength: payload.strength,
          image_reference: payload.image_reference,
          image_fidelity: payload.image_fidelity,
          human_fidelity: payload.human_fidelity,
          count: payload.count,
          size: payload.size || generateForm.size,
          aspect_ratio: payload.aspect_ratio || generateForm.aspect_ratio,
          reference_images: payload.referenceImages,
          style: payload.style || generateForm.style,
          style_preset_id:
            payload.style_preset_id || generateForm.style_preset_id,
          style_spec: payload.style_spec,
        },
      );
      if (!res.success || !res.data) {
        throw new Error(res.error || "图生图生成失败");
      }
      onTaskCreated?.(res.data.task_id);
      showAlert({
        title: "图生图任务已创建",
        message:
          "任务已在后台运行，完成后会自动刷新图片列表。是否前往任务管理页？",
        variant: "success",
        confirmText: "前往任务",
        onConfirm: () => router.push("/tasks"),
      });
      setVariantTarget(null);
      setVariantPrompt("");
      setVariantModalOpen(false);
    } catch (error) {
      console.error("Image-to-image generation failed:", error);
      showAlert({
        message: `图生图生成失败：${
          error instanceof Error ? error.message : "未知错误"
        }`,
        variant: "error",
      });
    } finally {
      setVariantSubmitting(false);
    }
  };

  return {
    variantTarget,
    setVariantTarget,
    variantPrompt,
    setVariantPrompt,
    variantModalOpen,
    setVariantModalOpen,
    variantSubmitting,
    variantReferenceSections,
    handleOpenVariant,
    handleSubmitVariant,
  };
}
