import { useEffect, useMemo, useState } from "react";

import type { AIModel, StyleSpec } from "@/utils/api";
import type { ImageGenAdvancedValue } from "../../imageGenAdvancedTypes";

interface UseImageToImageModalStateOptions {
  open: boolean;
  defaultSelected: string[];
  defaultPrompt: string;
  defaultModel: string;
  defaultGenerationProfileId: string;
  defaultCount: number;
  defaultSize: string;
  defaultAspectRatio: string;
  defaultStyle: string;
  defaultStylePresetId: string;
  defaultStyleSpec?: StyleSpec;
  defaultAdvancedValue?: ImageGenAdvancedValue;
}

export function useImageToImageModalState({
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
}: UseImageToImageModalStateOptions) {
  const [availableModels, setAvailableModels] = useState<AIModel[]>([]);
  const [loadedDefaultModel, setLoadedDefaultModel] = useState<string>("");
  const [selectedRefs, setSelectedRefs] = useState<string[]>(defaultSelected);
  const [prompt, setPrompt] = useState(defaultPrompt);
  const [modelIds, setModelIds] = useState<string[]>(
    defaultModel ? [defaultModel] : [],
  );
  const [generationProfile, setGenerationProfile] = useState<string>(
    defaultGenerationProfileId,
  );
  const [count, setCount] = useState(defaultCount);
  const [size, setSize] = useState(defaultSize);
  const [aspectRatio, setAspectRatio] = useState<string | undefined>(
    defaultAspectRatio || undefined,
  );
  const [style, setStyle] = useState(defaultStyle);
  const [stylePresetId, setStylePresetId] = useState(defaultStylePresetId);
  const [styleSpec, setStyleSpec] = useState<StyleSpec>(defaultStyleSpec ?? {});
  const [advanced, setAdvanced] = useState<ImageGenAdvancedValue>(
    defaultAdvancedValue ?? {},
  );
  const [previewImage, setPreviewImage] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setSelectedRefs(defaultSelected);
    setPrompt(defaultPrompt);
    setModelIds(defaultModel ? [defaultModel] : []);
    setGenerationProfile(defaultGenerationProfileId);
    setCount(defaultCount);
    setSize(defaultSize);
    setAspectRatio(defaultAspectRatio || undefined);
    setStyle(defaultStyle);
    setStylePresetId(defaultStylePresetId);
    setStyleSpec(defaultStyleSpec ?? {});
    setAdvanced(defaultAdvancedValue ?? {});
  }, [
    open,
    defaultSelected,
    defaultPrompt,
    defaultModel,
    defaultGenerationProfileId,
    defaultCount,
    defaultSize,
    defaultStyle,
    defaultStylePresetId,
    defaultStyleSpec,
    defaultAdvancedValue,
    defaultAspectRatio,
  ]);

  useEffect(() => {
    if (modelIds.length === 0 && loadedDefaultModel) {
      setModelIds([loadedDefaultModel]);
    }
  }, [loadedDefaultModel, modelIds.length]);

  const selectedModel = useMemo(() => {
    if (!modelIds[0]) return undefined;
    return availableModels.find((m) => m.model_id === modelIds[0]);
  }, [availableModels, modelIds]);

  const handleModelsLoaded = (loaded: AIModel[], defaultModelId: string) => {
    setAvailableModels(loaded);
    setLoadedDefaultModel(defaultModelId);
    if (modelIds.length === 0 && defaultModelId) {
      setModelIds([defaultModelId]);
    } else if (modelIds.length === 0 && loaded.length > 0) {
      setModelIds([loaded[0].model_id]);
    }
  };

  return {
    availableModels,
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
  };
}
