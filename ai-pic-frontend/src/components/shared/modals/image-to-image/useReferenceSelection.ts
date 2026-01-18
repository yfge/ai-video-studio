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

  const maxRefs = imageGenUi.maxReferenceImages;
  const allowMultipleRefs =
    maxRefs !== undefined
      ? maxRefs > 1
      : genMode !== "image_to_image" || imageGenUi.supportsExtraImages;

  useEffect(() => {
    if (maxRefs === undefined) {
      if (allowMultipleRefs) return;
      if (selectedRefs.length <= 1) return;
      setSelectedRefs([selectedRefs[0]]);
      return;
    }
    if (selectedRefs.length <= maxRefs) return;
    setSelectedRefs(selectedRefs.slice(-maxRefs));
  }, [allowMultipleRefs, maxRefs, selectedRefs, setSelectedRefs]);

  const notes = useMemo(() => {
    const next: string[] = [...(imageGenUi.notes || [])];
    if (referenceSectionsLength > 0 && !allowMultipleRefs) {
      next.unshift(
        "该模型不支持多参考图：将只使用 1 张参考图（其余选择会被替换/忽略）",
      );
    }
    if (
      referenceSectionsLength > 0 &&
      maxRefs !== undefined &&
      maxRefs > 1 &&
      !next.some((note) => note.includes(`${maxRefs} 张参考图`))
    ) {
      next.unshift(
        `该模型最多支持 ${maxRefs} 张参考图：超过上限会自动替换最早选择的参考图`,
      );
    }
    return next;
  }, [allowMultipleRefs, imageGenUi.notes, maxRefs, referenceSectionsLength]);

  const toggleReference = (url: string, options: { disabled: boolean }) => {
    if (options.disabled) return;
    setSelectedRefs((prev) => {
      if (prev.includes(url)) {
        return prev.filter((item) => item !== url);
      }
      if (!allowMultipleRefs) return [url];
      if (maxRefs === undefined) return [...prev, url];
      return [...prev, url].slice(-maxRefs);
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
