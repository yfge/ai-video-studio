"use client";

import { useCallback, useEffect } from "react";
import { useSearchParams } from "next/navigation";

export function useEpisodeGenerationAnchor(setGenOpen: (open: boolean) => void) {
  const searchParams = useSearchParams();

  const openEpisodeGeneration = useCallback(() => {
    setGenOpen(true);
    window.requestAnimationFrame(() => {
      document
        .getElementById("episode-generation")
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }, [setGenOpen]);

  useEffect(() => {
    if (searchParams.get("generate") === "episodes") {
      openEpisodeGeneration();
    }
  }, [openEpisodeGeneration, searchParams]);

  return openEpisodeGeneration;
}
