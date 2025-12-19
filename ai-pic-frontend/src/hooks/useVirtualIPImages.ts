"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  aiAPI,
  AIModelType,
  virtualIPAPI,
  virtualIPImageAPI,
  type AIImageGenerationRequest,
  type VirtualIP,
  type VirtualIPImage,
} from "@/utils/api";
import { useAvailableModels } from "@/hooks/useAvailableModels";
import { useStylePresets } from "@/hooks/useStylePresets";

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

export interface ImageGenerationFormState extends AIImageGenerationRequest {
  size?: string;
}

export interface UploadFormState {
  file: File | null;
  category: string;
  tags: string;
  is_default: boolean;
}

export const VIRTUAL_IP_STYLE_SPEC_FIELDS = [
  { key: "style_universe", label: "世界观 / 画风体系" },
  { key: "character_proportion", label: "人物比例" },
  { key: "character_face_style", label: "五官与人物风格" },
  { key: "line_art_style", label: "线稿风格" },
  { key: "color_render_style", label: "上色方式" },
  { key: "lighting_style", label: "阴影与光影" },
  { key: "color_mood", label: "色彩情绪" },
];

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");

export function resolveImageUrl(image: VirtualIPImage): string {
  if (image.oss_url) return image.oss_url;
  const fp = image.file_path || "";
  if (!fp) return "";
  if (fp.startsWith("http")) return fp;
  return `${API_BASE}${fp.startsWith("/") ? "" : "/"}${fp}`;
}

export function useVirtualIPImages({
  virtualIPKey,
  showAlert,
  router,
}: UseVirtualIPImagesOptions) {
  // Core state
  const [virtualIP, setVirtualIP] = useState<VirtualIP | null>(null);
  const [virtualIPId, setVirtualIPId] = useState<number | null>(null);
  const [images, setImages] = useState<VirtualIPImage[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [uploading, setUploading] = useState(false);

  // Preview state
  const [preview, setPreview] = useState<{
    src: string;
    alt?: string;
    description?: string;
  } | null>(null);

  // Form visibility
  const [showGenerateForm, setShowGenerateForm] = useState(false);

  // AI generation form
  const [generateForm, setGenerateForm] = useState<ImageGenerationFormState>({
    style: "realistic",
    style_preset_id: "",
    style_spec: {},
    category: "portrait",
    model: "",
    additional_prompts: "",
    is_default: false,
    count: 1,
    aspect_ratio: undefined,
  });

  // Upload form
  const [uploadForm, setUploadForm] = useState<UploadFormState>({
    file: null,
    category: "portrait",
    tags: "",
    is_default: false,
  });

  // Variant modal state
  const [variantTarget, setVariantTarget] = useState<VirtualIPImage | null>(null);
  const [variantPrompt, setVariantPrompt] = useState("");
  const [variantModalOpen, setVariantModalOpen] = useState(false);
  const [variantSubmitting, setVariantSubmitting] = useState(false);

  // Style presets
  const { presets: stylePresets } = useStylePresets();
  const selectedStylePreset = useMemo(() => {
    if (!generateForm.style_preset_id) return undefined;
    return stylePresets.find((p) => p.preset_id === generateForm.style_preset_id);
  }, [generateForm.style_preset_id, stylePresets]);

  // Models
  const fetchModels = useCallback(
    () => aiAPI.getAvailableModels({ type: AIModelType.ImageToImage }),
    [],
  );
  const { models: availableModels, defaultModel: recommendedModel } = useAvailableModels({
    fetcher: fetchModels,
    modelType: AIModelType.Image,
    cacheKey: `virtual-ip-image:${virtualIPId}`,
  });
  const selectedModel = availableModels.find(
    (model) => model.model_id === (generateForm.model || recommendedModel),
  );

  // Ensure form has valid model when models load
  useEffect(() => {
    if (generateForm.model) return;
    const firstModelId =
      recommendedModel || (availableModels.length > 0 ? availableModels[0].model_id : "");
    if (!firstModelId) return;
    setGenerateForm((prev) => (prev.model ? prev : { ...prev, model: firstModelId }));
  }, [availableModels, recommendedModel, generateForm.model]);

  // Model UI metadata
  const imageUi = ((selectedModel?.metadata as Record<string, unknown> | undefined)?.ui || {}) as Record<string, unknown>;
  const supportsAspectRatio = Boolean(imageUi.supports_aspect_ratio);

  const uiSizes = (imageUi.size_options as string[] | undefined)?.map((value) => ({
    value,
    label: value.toUpperCase?.() ? value.toUpperCase() : value,
  }));

  const resolutionOptions = useMemo(() => {
    if (uiSizes && uiSizes.length > 0) return uiSizes;
    if (selectedModel?.provider === "openai") {
      if (selectedModel.model_id === "dall-e-3") {
        return [
          { value: "1024x1024", label: "1024 x 1024" },
          { value: "1024x1792", label: "1024 x 1792 (portrait)" },
          { value: "1792x1024", label: "1792 x 1024 (landscape)" },
        ];
      }
      if (selectedModel.model_id === "dall-e-2") {
        return [
          { value: "256x256", label: "256 x 256" },
          { value: "512x512", label: "512 x 512" },
          { value: "1024x1024", label: "1024 x 1024" },
        ];
      }
    }
    if (selectedModel?.provider === "volcengine" && selectedModel.model_id === "seedream-4.5") {
      return [{ value: "2K", label: "2K (Seedream recommended)" }];
    }
    return [];
  }, [selectedModel, uiSizes]);

  const aspectRatioOptions = useMemo(() => {
    if (!supportsAspectRatio) return [];
    if (!Array.isArray(imageUi.aspect_ratio_options)) return [];
    return imageUi.aspect_ratio_options as string[];
  }, [imageUi.aspect_ratio_options, supportsAspectRatio]);

  // Sync aspect ratio with available options
  useEffect(() => {
    setGenerateForm((prev) => {
      if (!supportsAspectRatio || aspectRatioOptions.length === 0) {
        return prev.aspect_ratio ? { ...prev, aspect_ratio: undefined } : prev;
      }
      if (prev.aspect_ratio && aspectRatioOptions.includes(prev.aspect_ratio)) {
        return prev;
      }
      return { ...prev, aspect_ratio: aspectRatioOptions[0] };
    });
  }, [aspectRatioOptions, supportsAspectRatio]);

  // Data loading
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const ipResponse = await virtualIPAPI.getVirtualIP(virtualIPKey);

      if (ipResponse.success && ipResponse.data) {
        setVirtualIP(ipResponse.data);
        setVirtualIPId(ipResponse.data.id);

        const [imagesResponse, categoriesResponse] = await Promise.all([
          virtualIPImageAPI.getImages(ipResponse.data.id),
          virtualIPImageAPI.getCategories(ipResponse.data.id),
        ]);

        setImages(imagesResponse.success && imagesResponse.data ? imagesResponse.data : []);
        setCategories(categoriesResponse.success && categoriesResponse.data ? categoriesResponse.data : []);
      } else {
        showAlert({ message: "Failed to load virtual IP", variant: "error" });
        setImages([]);
        setCategories([]);
      }
    } catch (error) {
      console.error("Failed to load data:", error);
      showAlert({ message: "Failed to load data", variant: "error" });
      setImages([]);
      setCategories([]);
    } finally {
      setLoading(false);
    }
  }, [showAlert, virtualIPKey]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  // Filtered images
  const filteredImages = selectedCategory
    ? images.filter((img) => img.category === selectedCategory)
    : images;

  // Event handlers
  const handleGenerateImage = async () => {
    if (!virtualIPId) {
      showAlert({ message: "Virtual IP not loaded", variant: "error" });
      return;
    }
    try {
      setGenerating(true);
      const modelToUse =
        generateForm.model || recommendedModel || (availableModels.length > 0 ? availableModels[0].model_id : "");

      if (!modelToUse) {
        showAlert({ message: "Model list not loaded, please try again", variant: "warning" });
        return;
      }

      const response = await virtualIPImageAPI.generateImageAsync(virtualIPId, {
        ...generateForm,
        model: modelToUse,
        style_spec:
          generateForm.style_spec && Object.keys(generateForm.style_spec).length > 0
            ? generateForm.style_spec
            : undefined,
      });

      if (response.success && response.data) {
        setShowGenerateForm(false);
        setGenerateForm({
          style: "realistic",
          style_preset_id: "",
          style_spec: {},
          category: "portrait",
          model: recommendedModel || "",
          additional_prompts: "",
          is_default: false,
          count: 1,
          size: undefined,
          aspect_ratio: supportsAspectRatio ? aspectRatioOptions[0] || undefined : undefined,
        });
        showAlert({
          title: "Image generation task created",
          message: "Task is running in the background. Go to task management page?",
          variant: "success",
          confirmText: "Go to tasks",
          onConfirm: () => router.push("/tasks"),
        });
      } else {
        throw new Error(response.error || "AI image generation failed");
      }
    } catch (error) {
      console.error("AI image generation failed:", error);
      showAlert({
        message: `AI image generation failed: ${error instanceof Error ? error.message : "Unknown error"}`,
        variant: "error",
      });
    } finally {
      setGenerating(false);
    }
  };

  const handleUploadImage = async () => {
    if (!uploadForm.file) {
      showAlert({ message: "Please select a file", variant: "warning" });
      return;
    }
    if (!virtualIPId) {
      showAlert({ message: "Virtual IP not loaded", variant: "error" });
      return;
    }

    try {
      setUploading(true);
      const response = await virtualIPImageAPI.uploadImage(
        virtualIPId,
        uploadForm.file,
        uploadForm.category,
        uploadForm.tags,
        uploadForm.is_default,
      );

      if (response.success && response.data) {
        setImages((prev) => [response.data as VirtualIPImage, ...prev]);
        setUploadForm({ file: null, category: "portrait", tags: "", is_default: false });
        showAlert({ message: "Image uploaded successfully!", variant: "success" });
      } else {
        throw new Error(response.error || "Image upload failed");
      }
    } catch (error) {
      console.error("Image upload failed:", error);
      showAlert({
        message: `Image upload failed: ${error instanceof Error ? error.message : "Unknown error"}`,
        variant: "error",
      });
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteImage = (imageId: number) => {
    showAlert({
      title: "Confirm delete image",
      message: "Are you sure you want to delete this image?",
      variant: "warning",
      confirmText: "Delete",
      onConfirm: async () => {
        if (!virtualIPId) {
          showAlert({ message: "Virtual IP not loaded", variant: "error" });
          return;
        }
        try {
          const response = await virtualIPImageAPI.deleteImage(virtualIPId, imageId);
          if (response.success) {
            setImages((prev) => prev.filter((img) => img.id !== imageId));
            showAlert({ message: "Image deleted successfully", variant: "success" });
          } else {
            throw new Error(response.error || "Delete image failed");
          }
        } catch (error) {
          console.error("Delete image failed:", error);
          showAlert({
            message: `Delete image failed: ${error instanceof Error ? error.message : "Unknown error"}`,
            variant: "error",
          });
        }
      },
    });
  };

  const handleSetDefault = async (imageId: number) => {
    if (!virtualIPId) {
      showAlert({ message: "Virtual IP not loaded", variant: "error" });
      return;
    }
    try {
      const response = await virtualIPImageAPI.setDefaultImage(virtualIPId, imageId);
      if (response.success) {
        setImages((prev) => prev.map((img) => ({ ...img, is_default: img.id === imageId })));
        showAlert({ message: "Default image set successfully", variant: "success" });
      } else {
        throw new Error(response.error || "Set default image failed");
      }
    } catch (error) {
      console.error("Set default image failed:", error);
      showAlert({
        message: `Set default image failed: ${error instanceof Error ? error.message : "Unknown error"}`,
        variant: "error",
      });
    }
  };

  const handleOpenVariant = (image: VirtualIPImage) => {
    setVariantTarget(image);
    setVariantPrompt("Generate different angle/pose for this character, such as back view or full body");
    setVariantModalOpen(true);
  };

  const variantReferenceSections = useMemo(() => {
    if (!variantTarget) return [];
    const url = resolveImageUrl(variantTarget);
    return url ? [{ title: "Reference", images: [url] }] : [];
  }, [variantTarget]);

  const handleSubmitVariant = async (payload: {
    prompt: string;
    model?: string;
    count: number;
    size?: string;
    aspect_ratio?: string;
    style?: string;
    style_preset_id?: string;
    style_spec?: Record<string, unknown>;
    referenceImages: string[];
  }) => {
    if (!variantTarget || !virtualIPId) {
      showAlert({ message: "Virtual IP not loaded", variant: "error" });
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
      const res = await virtualIPImageAPI.generateVariantAndSaveAsync(virtualIPId, variantTarget.id, {
        prompt: payload.prompt || variantPrompt,
        model: modelFallback || undefined,
        count: payload.count,
        size: payload.size || generateForm.size,
        aspect_ratio: payload.aspect_ratio || generateForm.aspect_ratio,
        reference_images: payload.referenceImages,
        style: payload.style || generateForm.style,
        style_preset_id: payload.style_preset_id || generateForm.style_preset_id,
        style_spec: payload.style_spec,
      });
      if (!res.success || !res.data) {
        throw new Error(res.error || "Image-to-image generation failed");
      }
      showAlert({
        title: "Image-to-image task created",
        message: "Task is running in the background. Go to task management page?",
        variant: "success",
        confirmText: "Go to tasks",
        onConfirm: () => router.push("/tasks"),
      });
      setVariantTarget(null);
      setVariantPrompt("");
      setVariantModalOpen(false);
    } catch (error) {
      console.error("Image-to-image generation failed:", error);
      showAlert({
        message: `Image-to-image generation failed: ${error instanceof Error ? error.message : "Unknown error"}`,
        variant: "error",
      });
    } finally {
      setVariantSubmitting(false);
    }
  };

  return {
    // Core state
    virtualIP,
    virtualIPId,
    images,
    categories,
    selectedCategory,
    setSelectedCategory,
    loading,
    generating,
    uploading,
    filteredImages,

    // Preview
    preview,
    setPreview,

    // Form visibility
    showGenerateForm,
    setShowGenerateForm,

    // Generate form
    generateForm,
    setGenerateForm,
    stylePresets,
    selectedStylePreset,
    availableModels,
    recommendedModel,
    selectedModel,
    supportsAspectRatio,
    resolutionOptions,
    aspectRatioOptions,
    fetchModels,

    // Upload form
    uploadForm,
    setUploadForm,

    // Variant modal
    variantTarget,
    variantPrompt,
    variantModalOpen,
    setVariantModalOpen,
    variantSubmitting,
    variantReferenceSections,

    // Handlers
    handleGenerateImage,
    handleUploadImage,
    handleDeleteImage,
    handleSetDefault,
    handleOpenVariant,
    handleSubmitVariant,

    // Utils
    resolveImageUrl,
  };
}
