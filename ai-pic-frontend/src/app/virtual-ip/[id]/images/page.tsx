"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  aiAPI,
  AIModelType,
  virtualIPAPI,
  virtualIPImageAPI,
  type AIImageGenerationRequest,
  type VirtualIP,
  type VirtualIPImage,
} from "@/utils/api";
import {
  useAlertModal,
  ImageToImageModal,
  ImagePreviewModal,
} from "@/components/shared/modals";
import { useAvailableModels } from "@/hooks/useAvailableModels";
import {
  ImagePreviewCard,
  MultiModelSelector,
  StyleSpecAdvancedPanel,
  type StyleSpecField,
} from "@/components/shared";
import { useStylePresets } from "@/hooks/useStylePresets";

const VIRTUAL_IP_STYLE_SPEC_FIELDS: StyleSpecField[] = [
  { key: "style_universe", label: "世界观 / 画风体系" },
  { key: "character_proportion", label: "人物比例" },
  { key: "character_face_style", label: "五官与人物风格" },
  { key: "line_art_style", label: "线稿风格" },
  { key: "color_render_style", label: "上色方式" },
  { key: "lighting_style", label: "阴影与光影" },
  { key: "color_mood", label: "色彩情绪" },
];

export default function VirtualIPImagesPage() {
  const params = useParams();
  const router = useRouter();
  const virtualIPKey = params?.id?.toString() || "";
  const { showAlert } = useAlertModal();

  const [virtualIP, setVirtualIP] = useState<VirtualIP | null>(null);
  const [virtualIPId, setVirtualIPId] = useState<number | null>(null);
  const [images, setImages] = useState<VirtualIPImage[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState<{
    src: string;
    alt?: string;
    description?: string;
  } | null>(null);

  // 统一的后端基础地址（用于拼接本地文件路径）
  const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");

  const resolveImageUrl = useCallback(
    (image: VirtualIPImage) => {
      if (image.oss_url) return image.oss_url;
      const fp = image.file_path || "";
      if (!fp) return "";
      if (fp.startsWith("http")) return fp;
      return `${API_BASE}${fp.startsWith("/") ? "" : "/"}${fp}`;
    },
    [API_BASE],
  );

  // AI生成表单状态
  const [showGenerateForm, setShowGenerateForm] = useState(false);
  const [generateForm, setGenerateForm] = useState<AIImageGenerationRequest>({
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
  const { presets: stylePresets } = useStylePresets();
  const selectedStylePreset = useMemo(() => {
    if (!generateForm.style_preset_id) return undefined;
    return stylePresets.find(
      (p) => p.preset_id === generateForm.style_preset_id,
    );
  }, [generateForm.style_preset_id, stylePresets]);

  const fetchModels = useCallback(
    () => aiAPI.getAvailableModels({ type: AIModelType.ImageToImage }),
    [],
  );
  const { models: availableModels, defaultModel: recommendedModel } =
    useAvailableModels({
      fetcher: fetchModels,
      modelType: AIModelType.Image,
      cacheKey: `virtual-ip-image:${virtualIPId}`,
    });
  const selectedModel = availableModels.find(
    (model) => model.model_id === (generateForm.model || recommendedModel),
  );

  // 确保在模型列表加载完成后，表单中总有一个有效的模型 id
  useEffect(() => {
    if (generateForm.model) return;
    const firstModelId =
      recommendedModel ||
      (availableModels.length > 0 ? availableModels[0].model_id : "");
    if (!firstModelId) return;
    setGenerateForm((prev) =>
      prev.model ? prev : { ...prev, model: firstModelId },
    );
  }, [availableModels, recommendedModel, generateForm.model]);

  const imageUi = ((
    selectedModel?.metadata as Record<string, unknown> | undefined
  )?.ui || {}) as Record<string, unknown>;

  const supportsAspectRatio = Boolean(imageUi.supports_aspect_ratio);
  const uiSizes = (imageUi.size_options as string[] | undefined)?.map(
    (value) => ({
      value,
      label: value.toUpperCase?.() ? value.toUpperCase() : value,
    }),
  );

  // 根据模型决定可用分辨率选项（优先后端 metadata，其次官方已知模型）
  const resolutionOptions =
    uiSizes && uiSizes.length > 0
      ? uiSizes
      : selectedModel?.provider === "openai"
      ? selectedModel.model_id === "dall-e-3"
        ? [
            { value: "1024x1024", label: "1024 × 1024" },
            { value: "1024x1792", label: "1024 × 1792（竖版）" },
            { value: "1792x1024", label: "1792 × 1024（横版）" },
          ]
        : selectedModel.model_id === "dall-e-2"
        ? [
            { value: "256x256", label: "256 × 256" },
            { value: "512x512", label: "512 × 512" },
            { value: "1024x1024", label: "1024 × 1024" },
          ]
        : []
      : selectedModel?.provider === "volcengine" &&
        selectedModel.model_id === "seedream-4.5"
      ? [{ value: "2K", label: "2K（Seedream 推荐）" }]
      : [];

  const aspectRatioOptions = useMemo(
    () =>
      supportsAspectRatio &&
      Array.isArray(imageUi.aspect_ratio_options) &&
      (imageUi.aspect_ratio_options as string[]).length > 0
        ? (imageUi.aspect_ratio_options as string[])
        : [],
    [imageUi.aspect_ratio_options, supportsAspectRatio],
  );
  const aspectRatioKey = aspectRatioOptions.join("|");

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
  }, [aspectRatioKey, aspectRatioOptions, supportsAspectRatio]);

  // 上传表单状态
  const [uploadForm, setUploadForm] = useState({
    file: null as File | null,
    category: "portrait",
    tags: "",
    is_default: false,
  });

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

        if (imagesResponse.success && imagesResponse.data) {
          setImages(imagesResponse.data);
        } else {
          setImages([]);
        }

        if (categoriesResponse.success && categoriesResponse.data) {
          setCategories(categoriesResponse.data);
        } else {
          setCategories([]);
        }
      } else {
        showAlert({ message: "加载虚拟IP详情失败", variant: "error" });
        setImages([]);
        setCategories([]);
      }
    } catch (error) {
      console.error("加载数据失败:", error);
      showAlert({ message: "加载数据失败", variant: "error" });
      // 设置默认空值
      setImages([]);
      setCategories([]);
    } finally {
      setLoading(false);
    }
  }, [showAlert, virtualIPKey]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const handleGenerateImage = async () => {
    if (!virtualIPId) {
      showAlert({ message: "虚拟IP未加载", variant: "error" });
      return;
    }
    try {
      setGenerating(true);
      const modelToUse =
        generateForm.model ||
        recommendedModel ||
        (availableModels.length > 0 ? availableModels[0].model_id : "");

      if (!modelToUse) {
        showAlert({
          message: "模型列表尚未加载，请稍后再试",
          variant: "warning",
        });
        return;
      }

      const response = await virtualIPImageAPI.generateImageAsync(virtualIPId, {
        ...generateForm,
        model: modelToUse,
        style_spec:
          generateForm.style_spec &&
          Object.keys(generateForm.style_spec).length > 0
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
          aspect_ratio: supportsAspectRatio
            ? aspectRatioOptions[0] || undefined
            : undefined,
        });
        showAlert({
          title: "已创建图像生成任务",
          message: "任务会在后台异步执行，是否前往任务管理页面查看进度？",
          variant: "success",
          confirmText: "前往任务页",
          onConfirm: () => {
            router.push("/tasks");
          },
        });
      } else {
        throw new Error(response.error || "AI图像生成任务创建失败");
      }
    } catch (error) {
      console.error("AI图像生成失败:", error);
      showAlert({
        message: `AI图像生成失败: ${
          error instanceof Error ? error.message : "Unknown error"
        }`,
        variant: "error",
      });
    } finally {
      setGenerating(false);
    }
  };

  const handleUploadImage = async () => {
    if (!uploadForm.file) {
      showAlert({ message: "请选择文件", variant: "warning" });
      return;
    }
    if (!virtualIPId) {
      showAlert({ message: "虚拟IP未加载", variant: "error" });
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
        setUploadForm({
          file: null,
          category: "portrait",
          tags: "",
          is_default: false,
        });
        showAlert({ message: "图像上传成功！", variant: "success" });
      } else {
        throw new Error(response.error || "图像上传失败");
      }
    } catch (error) {
      console.error("图像上传失败:", error);
      showAlert({
        message: `图像上传失败: ${
          error instanceof Error ? error.message : "Unknown error"
        }`,
        variant: "error",
      });
    } finally {
      setUploading(false);
    }
  };

  const deleteImageById = async (imageId: number) => {
    if (!virtualIPId) {
      showAlert({ message: "虚拟IP未加载", variant: "error" });
      return;
    }
    try {
      const response = await virtualIPImageAPI.deleteImage(
        virtualIPId,
        imageId,
      );
      if (response.success) {
        setImages((prev) => prev.filter((img) => img.id !== imageId));
        showAlert({ message: "图像删除成功", variant: "success" });
      } else {
        throw new Error(response.error || "删除图像失败");
      }
    } catch (error) {
      console.error("删除图像失败:", error);
      showAlert({
        message: `删除图像失败: ${
          error instanceof Error ? error.message : "Unknown error"
        }`,
        variant: "error",
      });
    }
  };

  const handleDeleteImage = (imageId: number) => {
    showAlert({
      title: "确认删除图像",
      message: "确定要删除这张图像吗？",
      variant: "warning",
      confirmText: "删除",
      onConfirm: () => {
        void deleteImageById(imageId);
      },
    });
  };

  const handleSetDefault = async (imageId: number) => {
    if (!virtualIPId) {
      showAlert({ message: "虚拟IP未加载", variant: "error" });
      return;
    }
    try {
      const response = await virtualIPImageAPI.setDefaultImage(
        virtualIPId,
        imageId,
      );

      if (response.success) {
        setImages((prev) =>
          prev.map((img) => ({
            ...img,
            is_default: img.id === imageId,
          })),
        );
        showAlert({ message: "默认图像设置成功", variant: "success" });
      } else {
        throw new Error(response.error || "设置默认图像失败");
      }
    } catch (error) {
      console.error("设置默认图像失败:", error);
      showAlert({
        message: `设置默认图像失败: ${
          error instanceof Error ? error.message : "Unknown error"
        }`,
        variant: "error",
      });
    }
  };

  const filteredImages = selectedCategory
    ? images.filter((img) => img.category === selectedCategory)
    : images;

  const [variantTarget, setVariantTarget] = useState<VirtualIPImage | null>(
    null,
  );
  const [variantPrompt, setVariantPrompt] = useState("");
  const [variantModalOpen, setVariantModalOpen] = useState(false);
  const [variantSubmitting, setVariantSubmitting] = useState(false);

  const handleOpenVariant = (image: VirtualIPImage) => {
    setVariantTarget(image);
    setVariantPrompt("为当前角色生成不同视角/姿态的图像，如背面照或全身照");
    setVariantModalOpen(true);
  };

  const variantReferenceSections = useMemo(() => {
    if (!variantTarget) return [];
    const url = resolveImageUrl(variantTarget);
    return url ? [{ title: "参考图", images: [url] }] : [];
  }, [resolveImageUrl, variantTarget]);

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
      showAlert({ message: "虚拟IP未加载", variant: "error" });
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
      showAlert({
        title: "已创建图生图任务",
        message:
          "任务会在后台异步执行，生成完成后刷新本页即可看到新图像，是否前往任务管理页面查看进度？",
        variant: "success",
        confirmText: "前往任务页",
        onConfirm: () => {
          router.push("/tasks");
        },
      });
      setVariantTarget(null);
      setVariantPrompt("");
      setVariantModalOpen(false);
    } catch (error) {
      console.error("图生图生成失败:", error);
      showAlert({
        message: `图生图生成失败: ${
          error instanceof Error ? error.message : "Unknown error"
        }`,
        variant: "error",
      });
    } finally {
      setVariantSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (!virtualIP) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            虚拟IP不存在
          </h2>
          <button
            onClick={() => router.push("/virtual-ip")}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            返回列表
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 头部 */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {virtualIP.name} - 图像管理
              </h1>
              <p className="mt-2 text-gray-600">{virtualIP.description}</p>
            </div>
            <button
              onClick={() =>
                router.push(`/virtual-ip/${virtualIP.business_id}`)
              }
              className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
            >
              返回详情
            </button>
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="mb-6 flex gap-4">
          <button
            onClick={() => setShowGenerateForm(true)}
            className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2"
          >
            <span>🤖</span>
            AI生成图像
          </button>
          <button
            onClick={() => setShowGenerateForm(false)}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <span>📁</span>
            上传图像
          </button>
          <button
            onClick={() => router.push("/tasks")}
            className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 flex items-center gap-2"
          >
            <span>📋</span>
            查看任务
          </button>
        </div>

        {/* AI生成表单 */}
        {showGenerateForm && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4">🤖 AI图像生成</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <MultiModelSelector
                  label="AI模型"
                  value={generateForm.model ? [generateForm.model] : []}
                  onChange={(ids) =>
                    setGenerateForm((prev) => ({
                      ...prev,
                      model: ids[0] || "",
                    }))
                  }
                  modelType="image"
                  fetcher={fetchModels}
                  cacheKey={`virtual-ip-image:${virtualIPId}`}
                  allowAuto={false}
                  multiple={false}
                  autoSelectDefault
                  helperText="选择用于生成该图像的模型"
                  className="space-y-1"
                  onModelsLoaded={(_, defaultModel) => {
                    if (!generateForm.model && defaultModel) {
                      setGenerateForm((prev) => ({
                        ...prev,
                        model: defaultModel,
                      }));
                    }
                  }}
                />
                <p className="text-xs text-gray-500 mt-1">
                  {selectedModel?.capabilities?.join(", ") ||
                    "模型能力信息加载中"}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  生成风格
                </label>
                <select
                  value={generateForm.style}
                  onChange={(e) =>
                    setGenerateForm((prev) => ({
                      ...prev,
                      style: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="realistic">写实风格</option>
                  <option value="anime">动漫风格</option>
                  <option value="cartoon">卡通风格</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  风格预设
                </label>
                <select
                  value={generateForm.style_preset_id || ""}
                  onChange={(e) =>
                    setGenerateForm((prev) => ({
                      ...prev,
                      style_preset_id: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">（不使用预设）</option>
                  {stylePresets.map((preset) => (
                    <option key={preset.preset_id} value={preset.preset_id}>
                      {preset.label || preset.preset_id}
                    </option>
                  ))}
                </select>
                {selectedStylePreset?.description ? (
                  <p className="mt-1 text-xs text-gray-500">
                    {selectedStylePreset.description}
                  </p>
                ) : null}
              </div>
              <div className="md:col-span-3">
                <StyleSpecAdvancedPanel
                  fields={VIRTUAL_IP_STYLE_SPEC_FIELDS}
                  value={generateForm.style_spec || {}}
                  onChange={(next) =>
                    setGenerateForm((prev) => ({ ...prev, style_spec: next }))
                  }
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  图像类别
                </label>
                <select
                  value={generateForm.category}
                  onChange={(e) =>
                    setGenerateForm((prev) => ({
                      ...prev,
                      category: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="portrait">肖像</option>
                  <option value="full_body">全身像</option>
                  <option value="scene">场景</option>
                  <option value="action">动作</option>
                  <option value="emotion">表情</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  生成数量
                </label>
                <select
                  value={generateForm.count ?? 1}
                  onChange={(e) =>
                    setGenerateForm((prev) => ({
                      ...prev,
                      count: Number(e.target.value) || 1,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={1}>1 张</option>
                  <option value={2}>2 张</option>
                  <option value={3}>3 张</option>
                  <option value={4}>4 张</option>
                </select>
                <p className="mt-1 text-xs text-gray-500">
                  部分模型会为每次调用返回多张候选图像。
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  分辨率（部分模型可选）
                </label>
                <select
                  value={generateForm.size ?? ""}
                  onChange={(e) =>
                    setGenerateForm((prev) => ({
                      ...prev,
                      size: e.target.value || undefined,
                    }))
                  }
                  disabled={!resolutionOptions.length}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-400"
                >
                  {resolutionOptions.length === 0 ? (
                    <option value="">当前模型使用默认分辨率</option>
                  ) : (
                    <>
                      <option value="">自动（模型默认）</option>
                      {resolutionOptions.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </>
                  )}
                </select>
                {resolutionOptions.length > 0 && (
                  <p className="mt-1 text-xs text-gray-500">
                    选项来源于对应模型的官方文档（OpenAI / 火山方舟）。
                  </p>
                )}
              </div>
              {supportsAspectRatio ? (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    宽高比（部分模型可选）
                  </label>
                  <select
                    value={generateForm.aspect_ratio ?? ""}
                    onChange={(e) =>
                      setGenerateForm((prev) => ({
                        ...prev,
                        aspect_ratio: e.target.value || undefined,
                      }))
                    }
                    disabled={aspectRatioOptions.length === 0}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-400"
                  >
                    {aspectRatioOptions.length === 0 ? (
                      <option value="">当前模型未提供宽高比选项</option>
                    ) : (
                      <>
                        <option value="">自动（模型默认）</option>
                        {aspectRatioOptions.map((ratio) => (
                          <option key={ratio} value={ratio}>
                            {ratio}
                          </option>
                        ))}
                      </>
                    )}
                  </select>
                  {aspectRatioOptions.length > 0 ? (
                    <p className="mt-1 text-xs text-gray-500">
                      选项由后端模型元数据返回（兼容支持 aspect_ratio
                      的提供商）。
                    </p>
                  ) : null}
                </div>
              ) : null}
              <div className="md:col-span-3">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  额外提示词（可选，用逗号分隔）
                </label>
                <input
                  type="text"
                  value={generateForm.additional_prompts}
                  onChange={(e) =>
                    setGenerateForm((prev) => ({
                      ...prev,
                      additional_prompts: e.target.value,
                    }))
                  }
                  placeholder="例如：微笑，阳光，户外"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="md:col-span-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={generateForm.is_default}
                    onChange={(e) =>
                      setGenerateForm((prev) => ({
                        ...prev,
                        is_default: e.target.checked,
                      }))
                    }
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">设为默认图像</span>
                </label>
              </div>
            </div>
            <div className="mt-4 flex gap-2 flex-wrap">
              <button
                onClick={handleGenerateImage}
                disabled={generating}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {generating ? "提交中..." : "提交生成任务"}
              </button>
              <button
                onClick={() => setShowGenerateForm(false)}
                className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600"
              >
                取消
              </button>
            </div>
          </div>
        )}

        {/* 上传表单 */}
        {!showGenerateForm && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4">📁 上传图像</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  选择文件
                </label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) =>
                    setUploadForm((prev) => ({
                      ...prev,
                      file: e.target.files?.[0] || null,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  图像类别
                </label>
                <select
                  value={uploadForm.category}
                  onChange={(e) =>
                    setUploadForm((prev) => ({
                      ...prev,
                      category: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="portrait">肖像</option>
                  <option value="full_body">全身像</option>
                  <option value="scene">场景</option>
                  <option value="action">动作</option>
                  <option value="emotion">表情</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  标签（可选，用逗号分隔）
                </label>
                <input
                  type="text"
                  value={uploadForm.tags}
                  onChange={(e) =>
                    setUploadForm((prev) => ({ ...prev, tags: e.target.value }))
                  }
                  placeholder="例如：微笑，阳光，户外"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex items-center">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={uploadForm.is_default}
                    onChange={(e) =>
                      setUploadForm((prev) => ({
                        ...prev,
                        is_default: e.target.checked,
                      }))
                    }
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">设为默认图像</span>
                </label>
              </div>
            </div>
            <div className="mt-4">
              <button
                onClick={handleUploadImage}
                disabled={uploading || !uploadForm.file}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {uploading ? "上传中..." : "上传图像"}
              </button>
            </div>
          </div>
        )}

        {/* 分类筛选 */}
        <div className="mb-6">
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setSelectedCategory("")}
              className={`px-4 py-2 rounded-lg text-sm font-medium ${
                selectedCategory === ""
                  ? "bg-blue-600 text-white"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
            >
              全部
            </button>
            {categories.map((category) => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-4 py-2 rounded-lg text-sm font-medium ${
                  selectedCategory === category
                    ? "bg-blue-600 text-white"
                    : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        </div>

        {/* 图像网格 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {filteredImages.map((image) => {
            const primarySrc = image.oss_url
              ? image.oss_url
              : (() => {
                  const fp = image.file_path || "";
                  return fp.startsWith("http")
                    ? fp
                    : `${API_BASE}${fp.startsWith("/") ? "" : "/"}${fp}`;
                })();
            const fallbackSrc = (() => {
              const fp = image.file_path || "";
              return fp
                ? `${API_BASE}${fp.startsWith("/") ? "" : "/"}${fp}`
                : "";
            })();
            const isAiGenerated = Boolean(
              (
                image.metadata as
                  | { generation_method?: string }
                  | null
                  | undefined
              )?.generation_method,
            );

            return (
              <div
                key={image.id}
                className="bg-white rounded-lg shadow-md overflow-hidden"
              >
                <ImagePreviewCard
                  src={primarySrc}
                  fallbackSrc={fallbackSrc}
                  alt={`${virtualIP.name} - ${image.category}`}
                  aspectClass="aspect-[4/5]"
                  showActionsOnHover
                  badges={[
                    ...(image.is_default
                      ? [{ label: "默认", tone: "green" as const }]
                      : []),
                    ...(isAiGenerated
                      ? [{ label: "AI生成", tone: "blue" as const }]
                      : []),
                  ]}
                  onPreview={() =>
                    setPreview({
                      src: primarySrc,
                      alt: `${virtualIP.name} - ${image.category}`,
                      description: `${image.category} ｜ ${new Date(
                        image.created_at,
                      ).toLocaleString()}`,
                    })
                  }
                  onImg2Img={() => handleOpenVariant(image)}
                  onDelete={() => handleDeleteImage(image.id)}
                  actions={
                    image.is_default
                      ? []
                      : [
                          {
                            label: "设默认",
                            onClick: () => handleSetDefault(image.id),
                            tone: "primary",
                          },
                        ]
                  }
                />
                <div className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-900">
                      {image.category}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(image.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  {image.tags.length > 0 && (
                    <div className="mb-3">
                      <div className="flex flex-wrap gap-1">
                        {image.tags.slice(0, 3).map((tag, index) => (
                          <span
                            key={index}
                            className="bg-gray-100 text-gray-600 px-2 py-1 rounded text-xs"
                          >
                            {tag}
                          </span>
                        ))}
                        {image.tags.length > 3 && (
                          <span className="text-gray-500 text-xs">
                            +{image.tags.length - 3}
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                  {(() => {
                    const params = image.generation_params;
                    if (!params || Object.keys(params).length === 0)
                      return null;
                    const presetId =
                      typeof params.style_preset_id === "string"
                        ? params.style_preset_id
                        : null;
                    const spec = params.style_spec;
                    const resolution = params.style_spec_resolution;
                    if (!presetId && !spec && !resolution) return null;
                    return (
                      <details className="mb-3 rounded border border-gray-200 bg-gray-50 p-2 text-[11px] text-gray-700">
                        <summary className="cursor-pointer select-none text-xs font-medium text-gray-700">
                          风格详情
                        </summary>
                        <div className="mt-2 break-all">
                          preset: {presetId || "—"}
                        </div>
                        <div className="mt-1 break-all">
                          spec: {JSON.stringify(spec ?? null)}
                        </div>
                        <div className="mt-1 break-all">
                          resolution: {JSON.stringify(resolution ?? null)}
                        </div>
                      </details>
                    );
                  })()}
                </div>
              </div>
            );
          })}
        </div>

        <ImageToImageModal
          open={variantModalOpen && !!variantTarget}
          onClose={() => {
            setVariantModalOpen(false);
            setVariantTarget(null);
          }}
          title="图生图变体"
          description="参考图与提示词都会提交给图生图任务，可调整模型、分辨率与生成张数。"
          referenceSections={variantReferenceSections}
          defaultSelected={variantReferenceSections.flatMap(
            (section) => section.images,
          )}
          lockSelection
          defaultPrompt={variantPrompt}
          defaultModel={
            (variantTarget?.ai_model as string | undefined) ||
            generateForm.model ||
            recommendedModel ||
            ""
          }
          defaultCount={1}
          defaultSize={generateForm.size || ""}
          defaultAspectRatio={generateForm.aspect_ratio || ""}
          defaultStylePresetId={generateForm.style_preset_id || ""}
          defaultStyleSpec={generateForm.style_spec || {}}
          styleSpecFields={VIRTUAL_IP_STYLE_SPEC_FIELDS}
          modelType={AIModelType.ImageToImage}
          modelFetcher={() =>
            aiAPI.getAvailableModels({ type: AIModelType.ImageToImage })
          }
          modelCacheKey={`virtual-ip-img2img:${virtualIPId}`}
          submitting={variantSubmitting}
          onSubmit={handleSubmitVariant}
        />

        {filteredImages.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">🖼️</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">暂无图像</h3>
            <p className="text-gray-600">
              {selectedCategory ? `该分类下暂无图像` : "开始上传或生成图像吧！"}
            </p>
          </div>
        )}

        <ImagePreviewModal
          open={!!preview}
          src={preview?.src || ""}
          alt={preview?.alt}
          description={preview?.description}
          onClose={() => setPreview(null)}
        />
      </div>
    </div>
  );
}
