"use client";

import { useEffect, useMemo } from "react";

import type { AIModel } from "@/utils/api";
import { AIModelType } from "@/utils/api";
import { extractImageGenUi, type ImageGenMode } from "@/utils/modelUi";

interface UseReferenceSelectionOptions {
  modelType: string;
  model?: AIModel;
  referenceSectionsLength: number;
  selectedRefs: string[];
  setSelectedRefs: (next: string[] | ((prev: string[]) => string[])) => void;
}

export function useReferenceSelection({
  modelType,
  model,
  referenceSectionsLength,
  selectedRefs,
  setSelectedRefs,
}: UseReferenceSelectionOptions) {
  const genMode: ImageGenMode =
    modelType === AIModelType.ImageToImage ? "image_to_image" : "text_to_image";
  const imageGenUi = useMemo(
    () => extractImageGenUi(model, genMode),
    [genMode, model],
  );

  const allowMultipleRefs =
    genMode !== "image_to_image" || imageGenUi.supportsExtraImages;

  useEffect(() => {
    if (allowMultipleRefs) return;
    if (selectedRefs.length <= 1) return;
    setSelectedRefs([selectedRefs[0]]);
  }, [allowMultipleRefs, selectedRefs, setSelectedRefs]);

  const notes = useMemo(() => {
    const next: string[] = [...(imageGenUi.notes || [])];
    if (referenceSectionsLength > 0 && !allowMultipleRefs) {
      next.unshift(
        "该模型不支持多参考图：将只使用 1 张参考图（其余选择会被替换/忽略）",
      );
    }
    return next;
  }, [allowMultipleRefs, imageGenUi.notes, referenceSectionsLength]);

  const toggleReference = (url: string, options: { disabled: boolean }) => {
    if (options.disabled) return;
    setSelectedRefs((prev) => {
      if (prev.includes(url)) {
        return prev.filter((item) => item !== url);
      }
      return allowMultipleRefs ? [...prev, url] : [url];
    });
  };

  return {
    genMode,
    imageGenUi,
    allowMultipleRefs,
    notes,
    toggleReference,
  };
}
