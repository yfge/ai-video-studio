"use client";
import { useRouter } from "next/navigation";
import { aiAPI } from "@/utils/api/endpoints";
import { AIModelType, type VirtualIP } from "@/utils/api/types";
import {
  OperatorPanel,
  OperatorSectionHeader,
  OperatorState,
  operatorButtonClass,
} from "@/components/shared";
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
        <OperatorState title="加载图片管理中..." />
      </section>
    );
  }

  if (!activeVirtualIP) {
    return null;
  }

  return (
    <section id="ip-images" className="scroll-mt-24">
      <OperatorPanel>
        <OperatorSectionHeader
          title={`${activeVirtualIP.name} - 图片管理`}
          subtitle="按 IP 资产维护头像、半身、动作和参考图"
          action={
            <button
              type="button"
              onClick={() => router.push("/tasks")}
              className={operatorButtonClass("secondary")}
            >
              查看任务
            </button>
          }
        />
        <div className="grid gap-4 p-4 xl:grid-cols-[180px_minmax(0,1fr)_360px]">
          <aside className="space-y-4">
            <CategoryFilter
              categories={categories}
              selectedCategory={selectedCategory}
              onSelectCategory={setSelectedCategory}
            />
            <OperatorState
              title="迁移状态"
              detail="图片资产将随 IP 项目进入故事生产。"
              tone="blue"
            />
          </aside>
          <div>
            {loading ? (
              <OperatorState title="加载图片中..." />
            ) : (
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
            )}
          </div>
          <aside className="rounded-lg border border-gray-200 bg-white p-4">
            <div className="mb-4 flex gap-2">
              <button
                type="button"
                onClick={() => setShowGenerateForm(true)}
                className={operatorButtonClass(
                  showGenerateForm ? "primary" : "secondary",
                )}
              >
                生成图片
              </button>
              <button
                type="button"
                onClick={() => setShowGenerateForm(false)}
                className={operatorButtonClass(
                  !showGenerateForm ? "primary" : "secondary",
                )}
              >
                上传
              </button>
            </div>
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
          </aside>
        </div>

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
      </OperatorPanel>
    </section>
  );
}
