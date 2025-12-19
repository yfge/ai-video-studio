"use client";

import { useParams, useRouter } from "next/navigation";
import { AIModelType, aiAPI } from "@/utils/api";
import {
  useAlertModal,
  ImageToImageModal,
  ImagePreviewModal,
} from "@/components/shared/modals";
import {
  ImagePageHeader,
  ImageGenerationForm,
  ImageUploadForm,
  CategoryFilter,
  ImageGrid,
} from "@/components/features";
import {
  useVirtualIPImages,
  VIRTUAL_IP_STYLE_SPEC_FIELDS,
  resolveImageUrl,
} from "@/hooks/useVirtualIPImages";

export default function VirtualIPImagesPage() {
  const params = useParams();
  const router = useRouter();
  const virtualIPKey = params?.id?.toString() || "";
  const { showAlert } = useAlertModal();

  const state = useVirtualIPImages({
    virtualIPKey,
    showAlert,
    router,
  });

  const {
    virtualIP,
    virtualIPId,
    categories,
    selectedCategory,
    setSelectedCategory,
    loading,
    generating,
    uploading,
    filteredImages,
    preview,
    setPreview,
    showGenerateForm,
    setShowGenerateForm,
    generateForm,
    setGenerateForm,
    stylePresets,
    selectedStylePreset,
    selectedModel,
    supportsAspectRatio,
    resolutionOptions,
    aspectRatioOptions,
    uploadForm,
    setUploadForm,
    variantTarget,
    variantPrompt,
    variantModalOpen,
    setVariantModalOpen,
    variantSubmitting,
    variantReferenceSections,
    handleGenerateImage,
    handleUploadImage,
    handleDeleteImage,
    handleSetDefault,
    handleOpenVariant,
    handleSubmitVariant,
  } = state;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!virtualIP) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Virtual IP Not Found</h2>
          <button
            onClick={() => router.push("/virtual-ip")}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Back to List
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <ImagePageHeader
          virtualIP={virtualIP}
          onBack={() => router.push(`/virtual-ip/${virtualIP.business_id}`)}
          onShowGenerateForm={() => setShowGenerateForm(true)}
          onShowUploadForm={() => setShowGenerateForm(false)}
          onViewTasks={() => router.push("/tasks")}
        />

        {showGenerateForm ? (
          <ImageGenerationForm
            virtualIPId={virtualIPId}
            generateForm={generateForm}
            setGenerateForm={setGenerateForm}
            stylePresets={stylePresets}
            selectedStylePreset={selectedStylePreset}
            selectedModel={selectedModel}
            supportsAspectRatio={supportsAspectRatio}
            resolutionOptions={resolutionOptions}
            aspectRatioOptions={aspectRatioOptions}
            generating={generating}
            onGenerate={handleGenerateImage}
            onCancel={() => setShowGenerateForm(false)}
          />
        ) : (
          <ImageUploadForm
            uploadForm={uploadForm}
            setUploadForm={setUploadForm}
            uploading={uploading}
            onUpload={handleUploadImage}
          />
        )}

        <CategoryFilter
          categories={categories}
          selectedCategory={selectedCategory}
          onSelectCategory={setSelectedCategory}
        />

        <ImageGrid
          images={filteredImages}
          virtualIP={virtualIP}
          onPreview={(image) =>
            setPreview({
              src: resolveImageUrl(image),
              alt: `${virtualIP.name} - ${image.category}`,
              description: `${image.category} | ${new Date(image.created_at).toLocaleString()}`,
            })
          }
          onImg2Img={handleOpenVariant}
          onDelete={handleDeleteImage}
          onSetDefault={handleSetDefault}
        />

        <ImageToImageModal
          open={variantModalOpen && !!variantTarget}
          onClose={() => {
            setVariantModalOpen(false);
          }}
          title="Image-to-Image Variant"
          description="Reference image and prompt will be submitted to the image-to-image task. You can adjust model, resolution, and generation count."
          referenceSections={variantReferenceSections}
          defaultSelected={variantReferenceSections.flatMap((section) => section.images)}
          lockSelection
          defaultPrompt={variantPrompt}
          defaultModel={
            (variantTarget?.ai_model as string | undefined) ||
            generateForm.model ||
            ""
          }
          defaultCount={1}
          defaultSize={generateForm.size || ""}
          defaultAspectRatio={generateForm.aspect_ratio || ""}
          defaultStylePresetId={generateForm.style_preset_id || ""}
          defaultStyleSpec={generateForm.style_spec || {}}
          styleSpecFields={VIRTUAL_IP_STYLE_SPEC_FIELDS}
          modelType={AIModelType.ImageToImage}
          modelFetcher={() => aiAPI.getAvailableModels({ type: AIModelType.ImageToImage })}
          modelCacheKey={`virtual-ip-img2img:${virtualIPId}`}
          submitting={variantSubmitting}
          onSubmit={handleSubmitVariant}
        />

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
