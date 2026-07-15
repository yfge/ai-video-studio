"use client";

import { useEffect, useState } from "react";
import type { TimelineVideoReferenceChoice } from "./TimelineClipProviderReworkModel";

export function useTimelineClipVideoReferenceChoice(
  clipId: string | null | undefined,
  storyboardReady: boolean,
) {
  const [choice, setChoice] =
    useState<TimelineVideoReferenceChoice>("start_end");
  useEffect(() => {
    setChoice(storyboardReady ? "clip_storyboard_sheet" : "start_end");
  }, [clipId, storyboardReady]);
  const storyboardChoice = [
    "clip_storyboard_sheet",
    "clip_storyboard_panel",
  ].includes(choice);
  return {
    choice,
    setChoice,
    effectiveChoice:
      storyboardChoice && !storyboardReady ? "start_end" : choice,
  } as const;
}
