"use client";

import { OperatorPanel } from "@/components/shared";
import { EpisodeGeneratePanel } from "@/components/features/story-detail/EpisodeGeneratePanel";
import { useStoryDetail } from "@/hooks/useStoryDetail";

export function StoryDetailEpisodeGeneration({
  state,
}: {
  state: ReturnType<typeof useStoryDetail>;
}) {
  return (
    <OperatorPanel id="episode-generation" className="scroll-mt-24 p-5">
      <EpisodeGeneratePanel
        genOpen={state.genOpen}
        setGenOpen={state.setGenOpen}
        genForm={state.genForm}
        setGenForm={state.setGenForm}
        useAsync={state.useAsync}
        setUseAsync={state.setUseAsync}
        promptPreview={state.promptPreview}
        onPreviewPrompt={state.handlePreviewPrompt}
        onGenerate={state.handleGenerateEpisodes}
        canGenerate={state.canGenerate}
        episodesTask={state.episodesTask}
        contextPackPreviewProps={{
          includeContinuityLedger: state.includeContinuityLedger,
          setIncludeContinuityLedger: state.setIncludeContinuityLedger,
          includeCharacterCards: state.includeCharacterCards,
          setIncludeCharacterCards: state.setIncludeCharacterCards,
          recentEpisodesCount: state.recentEpisodesCount,
          setRecentEpisodesCount: state.setRecentEpisodesCount,
          contextPackPreview: state.contextPackPreview,
          contextPackLoading: state.contextPackLoading,
          contextPackError: state.contextPackError,
          onPreviewContextPack: state.handlePreviewContextPack,
        }}
      />
    </OperatorPanel>
  );
}
