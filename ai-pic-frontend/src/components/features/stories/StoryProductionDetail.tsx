"use client";

import Link from "next/link";
import {
  OperatorPanel,
  OperatorSectionHeader,
  OperatorState,
  StatusPill,
  operatorButtonClass,
  operatorTableClass,
  operatorTableHeadClass,
  operatorTableRowClass,
} from "@/components/shared";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import { EpisodeGeneratePanel } from "@/components/features/story-detail/EpisodeGeneratePanel";
import { StoryReadinessPanel } from "@/components/features/story-detail/StoryReadinessPanel";
import { useStoryDetail } from "@/hooks/useStoryDetail";
import type { StoryCharacter } from "@/utils/api/types";
import { episodeWorkspaceHref } from "@/utils/routes";
import {
  formatStoryTime,
  hasStoryboard,
  hasTimeline,
  latestScript,
  storyDisplayText,
} from "./StoryProductionModel";

export function StoryProductionDetail({ storyKey }: { storyKey: string }) {
  const { showAlert } = useAlertModal();
  const state = useStoryDetail({ storyKey, showAlert });
  const {
    story,
    episodes,
    scriptsByEpisode,
    loading,
    loadingScripts,
    genOpen,
    setGenOpen,
    genForm,
    setGenForm,
    promptPreview,
    useAsync,
    setUseAsync,
    vips,
    focusCharacters,
    includeContinuityLedger,
    setIncludeContinuityLedger,
    includeCharacterCards,
    setIncludeCharacterCards,
    recentEpisodesCount,
    setRecentEpisodesCount,
    contextPackPreview,
    contextPackLoading,
    contextPackError,
    handlePreviewPrompt,
    handlePreviewContextPack,
    handleGenerateEpisodes,
    toggleFocusCharacter,
    readiness,
    readinessLoading,
    readinessError,
    quickFixLoading,
    canGenerate,
    checkReadiness,
    runQuickFix,
  } = state;

  if (loading) {
    return <OperatorState title="加载故事详情..." />;
  }

  if (!story) {
    return <OperatorState title="故事不存在或无权访问。" tone="red" />;
  }

  const linkedCharacters = story.story_characters || story.characters || [];

  return (
    <div className="grid gap-5 2xl:grid-cols-[minmax(0,1fr)_360px]">
      <section className="space-y-5">
        <OperatorPanel className="p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-lg font-semibold text-gray-950">
                  {story.title}
                </h1>
                <StatusPill tone="green">{story.status}</StatusPill>
              </div>
              <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-500">
                <span>{story.genre}</span>
                {story.theme ? <span>{story.theme}</span> : null}
                {story.duration_minutes ? (
                  <span>{story.duration_minutes} 分钟</span>
                ) : null}
                <span>更新 {formatStoryTime(story.updated_at)}</span>
              </div>
            </div>
            <button className={operatorButtonClass("secondary")}>
              编辑故事
            </button>
          </div>
          <p className="mt-4 line-clamp-6 max-w-3xl text-sm leading-6 text-gray-700">
            {storyDisplayText(story.synopsis, story.premise)}
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {linkedCharacters.length ? (
              linkedCharacters.map((character) => (
                <CharacterChip key={character.id} character={character} />
              ))
            ) : (
              <span className="rounded-md border border-amber-200 bg-amber-50 px-2 py-1 text-xs text-amber-700">
                IP 关联待迁移
              </span>
            )}
          </div>
        </OperatorPanel>

        <OperatorPanel>
          <OperatorSectionHeader
            title="剧集生产状态"
            action={
              <span className="text-xs text-gray-500">
                {loadingScripts ? "剧本加载中" : `共 ${episodes.length} 集`}
              </span>
            }
          />
          <div className="overflow-x-auto">
            <table className={`${operatorTableClass} min-w-[760px]`}>
              <thead className={operatorTableHeadClass}>
                <tr>
                  <th className="px-5 py-3 text-left font-medium">集数</th>
                  <th className="px-4 py-3 text-left font-medium">标题</th>
                  <th className="px-4 py-3 text-left font-medium">剧本</th>
                  <th className="px-4 py-3 text-left font-medium">时间轴</th>
                  <th className="px-4 py-3 text-left font-medium">分镜</th>
                  <th className="px-5 py-3 text-right font-medium">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {episodes.map((episode) => {
                  const script = latestScript(scriptsByEpisode[episode.id] || []);
                  const timelineReady = hasTimeline(episode, script);
                  const storyboardReady = hasStoryboard(script);
                  return (
                    <tr key={episode.id} className={operatorTableRowClass}>
                      <td className="px-5 py-4 font-medium">
                        第{episode.episode_number}集
                      </td>
                      <td className="px-4 py-4">{episode.title}</td>
                      <ReadyCell ready={Boolean(script)} />
                      <ReadyCell ready={timelineReady} />
                      <ReadyCell ready={storyboardReady} />
                      <td className="px-5 py-4 text-right">
                        <Link
                          href={episodeWorkspaceHref(
                            episode.business_id || episode.id,
                            { tab: "timeline", scriptId: script?.id },
                          )}
                          className={operatorButtonClass("primary", "whitespace-nowrap")}
                        >
                          进入时间轴
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </OperatorPanel>
      </section>

      <aside className="space-y-5">
        <OperatorPanel className="p-5">
          <h2 className="text-sm font-semibold">IP 生产准备</h2>
          <div className="mt-4">
            <StoryReadinessPanel
              readiness={readiness}
              loading={readinessLoading}
              error={readinessError}
              quickFixLoading={quickFixLoading}
              onRefreshReadiness={checkReadiness}
              onQuickFix={runQuickFix}
            />
          </div>
        </OperatorPanel>
        <EpisodeGeneratePanel
          genOpen={genOpen}
          setGenOpen={setGenOpen}
          genForm={genForm}
          setGenForm={setGenForm}
          vips={vips}
          focusCharacters={focusCharacters}
          onToggleFocusCharacter={toggleFocusCharacter}
          useAsync={useAsync}
          setUseAsync={setUseAsync}
          promptPreview={promptPreview}
          onPreviewPrompt={handlePreviewPrompt}
          onGenerate={handleGenerateEpisodes}
          canGenerate={canGenerate}
          contextPackPreviewProps={{
            includeContinuityLedger,
            setIncludeContinuityLedger,
            includeCharacterCards,
            setIncludeCharacterCards,
            recentEpisodesCount,
            setRecentEpisodesCount,
            contextPackPreview,
            contextPackLoading,
            contextPackError,
            onPreviewContextPack: handlePreviewContextPack,
          }}
        />
      </aside>
    </div>
  );
}

function ReadyCell({ ready }: { ready: boolean }) {
  return (
    <td className="px-4 py-4">
      <StatusPill tone={ready ? "green" : "gray"}>
        {ready ? "已就绪" : "未开始"}
      </StatusPill>
    </td>
  );
}

function CharacterChip({ character }: { character: StoryCharacter }) {
  const name = character.character_name || character.name || "未命名 IP";
  return (
    <span className="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs text-gray-600">
      IP: {name}
    </span>
  );
}
