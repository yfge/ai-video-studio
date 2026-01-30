"use client";
import { useRouter } from "next/navigation";
import { AIModelType, aiAPI, type VirtualIP } from "@/utils/api";
import {
  ImagePreviewModal,
  ImageToImageModal,
  useAlertModal,
} from "@/components/shared/modals";
import {
  resolveImageUrl,
  useVirtualIPImages,
  VIRTUAL_IP_STYLE_SPEC_FIELDS,
} from "@/hooks/useVirtualIPImages";
import { CategoryFilter } from "./CategoryFilter";
import { ImageGenerationForm } from "./ImageGenerationForm";
import { ImageGrid } from "./ImageGrid";
import { ImagePageHeader } from "./ImagePageHeader";
import { ImageUploadForm } from "./ImageUploadForm";
interface VirtualIPImageManagerProps {
  virtualIPKey: string;
  virtualIP?: VirtualIP | null;
}
export function VirtualIPImageManager({
  virtualIPKey,
  virtualIP,
}: VirtualIPImageManagerProps) {
  const router = useRouter();
  const { showAlert } = useAlertModal();
  const state = useVirtualIPImages({
    virtualIPKey,
    virtualIP,
    skipVirtualIPFetch: Boolean(virtualIP),
    showAlert,
    router,
  });

  const {
    virtualIP: fetchedVirtualIP,
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

  const activeVirtualIP = virtualIP || fetchedVirtualIP;

  if (!activeVirtualIP && loading) {
    return (
      <section id="ip-images" className="scroll-mt-24">
        <div className="bg-white shadow-sm ring-1 ring-gray-200 rounded-2xl overflow-hidden">
          <div className="p-6 sm:p-8 flex items-center justify-center gap-3 text-gray-600">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span>加载图片管理中...</span>
          </div>
        </div>
      </section>
    );
  }

  if (!activeVirtualIP) {
    return null;
  }

  return (
    <section id="ip-images" className="scroll-mt-24">
      <div className="bg-white shadow-sm ring-1 ring-gray-200 rounded-2xl overflow-hidden">
        <div className="p-6 sm:p-8">
          <ImagePageHeader
            virtualIP={activeVirtualIP}
            showVirtualIPInfo={false}
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

          {loading ? (
            <div className="py-10 flex items-center justify-center gap-3 text-gray-500">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
              <span>加载图片中...</span>
            </div>
          ) : (
            <>
              <CategoryFilter
                categories={categories}
                selectedCategory={selectedCategory}
                onSelectCategory={setSelectedCategory}
              />

              <ImageGrid
                images={filteredImages}
                virtualIP={activeVirtualIP}
                onPreview={(image) =>
                  setPreview({
                    src: resolveImageUrl(image),
                    alt: `${activeVirtualIP.name} - ${image.category}`,
                    description: `${image.category} | ${new Date(
                      image.created_at,
                    ).toLocaleString()}`,
                  })
                }
                onImg2Img={handleOpenVariant}
                onDelete={handleDeleteImage}
                onSetDefault={handleSetDefault}
              />
            </>
          )}

          <ImageToImageModal
            open={variantModalOpen && !!variantTarget}
            onClose={() => {
              setVariantModalOpen(false);
            }}
            title="图生图变体"
            description="将参考图与提示词提交到图生图任务，可调整模型、分辨率与生成数量。"
            referenceSections={variantReferenceSections}
            defaultSelected={variantReferenceSections.flatMap(
              (section) => section.images,
            )}
            lockSelection
            defaultPrompt={variantPrompt}
            defaultModel={
              (variantTarget?.ai_model as string | undefined) ||
              generateForm.model ||
              ""
            }
            defaultGenerationProfileId={generateForm.generation_profile || ""}
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
            showAdvancedParams
            defaultAdvancedValue={{
              seed: generateForm.seed,
              steps: generateForm.steps,
              cfg_scale: generateForm.cfg_scale,
            }}
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
    </section>
  );
}
