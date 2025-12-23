"use client";

import { useState } from "react";

import { useVirtualIPImageActions } from "./virtual-ip/useVirtualIPImageActions";
import { useVirtualIPImageData } from "./virtual-ip/useVirtualIPImageData";
import { useVirtualIPImageGeneration } from "./virtual-ip/useVirtualIPImageGeneration";
import { useVirtualIPImageUpload } from "./virtual-ip/useVirtualIPImageUpload";
import { useVirtualIPImageVariants } from "./virtual-ip/useVirtualIPImageVariants";

export { VIRTUAL_IP_STYLE_SPEC_FIELDS, resolveImageUrl } from "./virtual-ip/virtualIpImageConstants";
export type { ImageGenerationFormState, UploadFormState } from "./virtual-ip/virtualIpImageTypes";

export interface UseVirtualIPImagesOptions {
  virtualIPKey: string;
  showAlert: (opts: {
    message: string;
    variant: "success" | "error" | "warning" | "info";
    title?: string;
    confirmText?: string;
    onConfirm?: () => void;
  }) => void;
  router: { push: (path: string) => void };
}

export function useVirtualIPImages({
  virtualIPKey,
  showAlert,
  router,
}: UseVirtualIPImagesOptions) {
  const data = useVirtualIPImageData({ virtualIPKey, showAlert });
  const generation = useVirtualIPImageGeneration({
    virtualIPId: data.virtualIPId,
    showAlert,
    router,
  });
  const upload = useVirtualIPImageUpload({
    virtualIPId: data.virtualIPId,
    setImages: data.setImages,
    showAlert,
  });
  const actions = useVirtualIPImageActions({
    virtualIPId: data.virtualIPId,
    setImages: data.setImages,
    showAlert,
  });
  const variants = useVirtualIPImageVariants({
    virtualIPId: data.virtualIPId,
    generateForm: generation.generateForm,
    recommendedModel: generation.recommendedModel,
    showAlert,
    router,
  });

  const [preview, setPreview] = useState<{
    src: string;
    alt?: string;
    description?: string;
  } | null>(null);

  return {
    virtualIP: data.virtualIP,
    virtualIPId: data.virtualIPId,
    images: data.images,
    categories: data.categories,
    selectedCategory: data.selectedCategory,
    setSelectedCategory: data.setSelectedCategory,
    loading: data.loading,
    filteredImages: data.filteredImages,

    preview,
    setPreview,

    showGenerateForm: generation.showGenerateForm,
    setShowGenerateForm: generation.setShowGenerateForm,

    generateForm: generation.generateForm,
    setGenerateForm: generation.setGenerateForm,
    stylePresets: generation.stylePresets,
    selectedStylePreset: generation.selectedStylePreset,
    availableModels: generation.availableModels,
    recommendedModel: generation.recommendedModel,
    selectedModel: generation.selectedModel,
    supportsAspectRatio: generation.supportsAspectRatio,
    resolutionOptions: generation.resolutionOptions,
    aspectRatioOptions: generation.aspectRatioOptions,
    generating: generation.generating,
    fetchModels: generation.fetchModels,

    uploadForm: upload.uploadForm,
    setUploadForm: upload.setUploadForm,
    uploading: upload.uploading,

    variantTarget: variants.variantTarget,
    variantPrompt: variants.variantPrompt,
    variantModalOpen: variants.variantModalOpen,
    variantSubmitting: variants.variantSubmitting,
    variantReferenceSections: variants.variantReferenceSections,

    handleGenerateImage: generation.handleGenerateImage,
    handleUploadImage: upload.handleUploadImage,
    handleDeleteImage: actions.handleDeleteImage,
    handleSetDefault: actions.handleSetDefault,
    handleOpenVariant: variants.handleOpenVariant,
    handleSubmitVariant: variants.handleSubmitVariant,
    setVariantModalOpen: variants.setVariantModalOpen,
  };
}
