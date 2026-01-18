"use client";
import { useMemo } from "react";
import { useStylePresets } from "@/hooks/useStylePresets";
import { extractImageUi } from "@/utils/modelUi";
import { AIModelType } from "@/utils/api";
import { GenerationAuditWarnings } from "../GenerationAuditWarnings";
import { ImageGenAdvancedFields } from "../ImageGenAdvancedFields";
import { ImageToImageReferencePicker } from "./image-to-image/ImageToImageReferencePicker";
import { ImageToImagePreviewOverlay } from "./image-to-image/ImageToImagePreviewOverlay";
import { ImageToImageSettingsForm } from "./image-to-image/ImageToImageSettingsForm";
import { buildLabeledReferences } from "./image-to-image/referenceUtils";
import type { ImageToImageModalProps } from "./image-to-image/types";
import { useImageToImageModalState } from "./image-to-image/useImageToImageModalState";
import { useReferenceSelection } from "./image-to-image/useReferenceSelection";

export function ImageToImageModal({
  open,
  title = "图生图",
  description,
  referenceSections = [],
  defaultSelected = [],
  lockSelection = false,
  defaultPrompt = "",
  defaultModel = "",
  defaultGenerationProfileId = "",
  defaultCount = 1,
  defaultSize = "",
  defaultAspectRatio = "",
  defaultStyle = "realistic",
  defaultStylePresetId = "",
  defaultStyleSpec,
  showAdvancedParams = false,
  defaultAdvancedValue,
  minCount = 1,
  maxCount = 4,
  modelType = AIModelType.ImageToImage,
  modelFetcher,
  modelCacheKey,
  styleOptions,
  showStylePreset = true,
  styleSpecFields,
  extraContent,
  submitting = false,
  onClose,
  onSubmit,
}: ImageToImageModalProps) {
  const submitLabel =
    modelType === AIModelType.ImageToImage ? "提交图生图任务" : "提交生成任务";
  const {
    selectedModel,
    handleModelsLoaded,
    selectedRefs,
    setSelectedRefs,
    prompt,
    setPrompt,
    modelIds,
    setModelIds,
    generationProfile,
    setGenerationProfile,
    count,
    setCount,
    size,
    setSize,
    aspectRatio,
    setAspectRatio,
    style,
    setStyle,
    stylePresetId,
    setStylePresetId,
    styleSpec,
    setStyleSpec,
    advanced,
    setAdvanced,
    previewImage,
    setPreviewImage,
  } = useImageToImageModalState({
    open,
    defaultSelected,
    defaultPrompt,
    defaultModel,
    defaultGenerationProfileId,
    defaultCount,
    defaultSize,
    defaultAspectRatio,
    defaultStyle,
    defaultStylePresetId,
    defaultStyleSpec,
    defaultAdvancedValue,
  });
  const { presets: stylePresets } = useStylePresets({
    enabled: showStylePreset,
  });
  const selectedStylePreset = useMemo(() => {
    if (!stylePresetId) return undefined;
    return stylePresets.find((p) => p.preset_id === stylePresetId);
  }, [stylePresets, stylePresetId]);
  const imageUi = useMemo(() => extractImageUi(selectedModel), [selectedModel]);
  const supportsAspectRatio = imageUi.supportsAspectRatio;
  const { genMode, notes: modalNotes, toggleReference } =
    useReferenceSelection({
      modelType,
      model: selectedModel,
      referenceSectionsLength: referenceSections.length,
      selectedRefs,
      setSelectedRefs,
    });
  const handleSubmit = async () => {
    const refs = referenceSections.length > 0 ? selectedRefs : [];
    const labeledRefs = buildLabeledReferences(refs, referenceSections);
    await onSubmit({
      prompt: prompt.trim(),
      model: modelIds[0],
      generation_profile: generationProfile || undefined,
      count: Math.max(minCount, Math.min(maxCount, count || minCount)),
      size: size || undefined,
      aspect_ratio: supportsAspectRatio ? aspectRatio || undefined : undefined,
      style: style || undefined,
      style_preset_id: stylePresetId || undefined,
      style_spec:
        styleSpec && Object.keys(styleSpec).length > 0 ? styleSpec : undefined,
      referenceImages: refs,
      labeledReferences: labeledRefs.length > 0 ? labeledRefs : undefined,
      seed: advanced.seed,
      steps: advanced.steps,
      cfg_scale: advanced.cfg_scale,
      negative_prompt: advanced.negative_prompt,
      strength: advanced.strength,
      image_reference: advanced.image_reference,
      image_fidelity: advanced.image_fidelity,
      human_fidelity: advanced.human_fidelity,
    });
  };
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-3 py-6">
      <div className="w-full max-w-5xl overflow-auto rounded-xl bg-white p-5 shadow-2xl max-h-full">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            {description ? (
              <p className="mt-1 text-xs text-gray-600">{description}</p>
            ) : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            关闭
          </button>
        </div>

        <ImageToImageReferencePicker
          referenceSections={referenceSections}
          selectedRefs={selectedRefs}
          lockSelection={lockSelection}
          onToggle={(url) => toggleReference(url, { disabled: lockSelection })}
          onPreview={setPreviewImage}
        />

        <ImageToImageSettingsForm
          prompt={prompt}
          onPromptChange={setPrompt}
          modelIds={modelIds}
          onModelIdsChange={setModelIds}
          modelType={modelType}
          modelFetcher={modelFetcher}
          modelCacheKey={modelCacheKey}
          onModelsLoaded={handleModelsLoaded}
          selectedModel={selectedModel}
          generationProfile={generationProfile}
          onGenerationProfileChange={setGenerationProfile}
          count={count}
          onCountChange={setCount}
          minCount={minCount}
          maxCount={maxCount}
          style={style}
          onStyleChange={setStyle}
          styleOptions={styleOptions}
          showStylePreset={showStylePreset}
          stylePresets={stylePresets}
          stylePresetId={stylePresetId}
          onStylePresetIdChange={setStylePresetId}
          selectedStylePreset={selectedStylePreset}
          styleSpecFields={styleSpecFields}
          styleSpec={styleSpec}
          onStyleSpecChange={setStyleSpec}
          size={size}
          aspectRatio={aspectRatio}
          onDimensionsChange={(next) => {
            if (next.size !== undefined) setSize(next.size || "");
            if (next.aspect_ratio !== undefined)
              setAspectRatio(next.aspect_ratio || undefined);
          }}
        />

        {modalNotes.length > 0 ? (
          <GenerationAuditWarnings
            title="模型提示"
            warnings={modalNotes}
            className="mt-4"
          />
        ) : null}

        {showAdvancedParams ? (
          <div className="mt-4 border-t pt-4">
            <ImageGenAdvancedFields
              mode={genMode}
              model={selectedModel}
              value={advanced}
              onChange={setAdvanced}
              disabled={submitting}
            />
          </div>
        ) : null}

        {extraContent ? (
          <div className="mt-4 border-t pt-4">{extraContent}</div>
        ) : null}

        <div className="mt-4 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-2 text-sm rounded border border-gray-300 text-gray-700 hover:bg-gray-50"
            disabled={submitting}
          >
            取消
          </button>
          <button
            type="button"
            onClick={() => void handleSubmit()}
            disabled={
              submitting ||
              (referenceSections.length > 0 && selectedRefs.length === 0)
            }
            className="px-4 py-2 text-sm font-medium rounded bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {submitting ? "提交中..." : submitLabel}
          </button>
        </div>
      </div>

      <ImageToImagePreviewOverlay
        src={previewImage}
        onClose={() => setPreviewImage(null)}
      />
    </div>
  );
}
