"use client";

import Link from "next/link";
import {
  OperatorPanel,
  OperatorInspector,
  OperatorMainCanvas,
  OperatorSectionHeader,
  OperatorState,
  OperatorWorkspace,
  StatusPill,
  operatorButtonClass,
  operatorTableClass,
  operatorTableHeadClass,
  operatorTableRowClass,
} from "@/components/shared";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import { StoryNovelExportPanel } from "@/components/features/story-detail/StoryNovelExportPanel";
import { StoryNovelWorkflowPanel } from "@/components/features/story-detail/StoryNovelWorkflowPanel";
import { StoryReadinessPanel } from "@/components/features/story-detail/StoryReadinessPanel";
import { useStoryDetail } from "@/hooks/useStoryDetail";
import { episodeWorkspaceHref } from "@/utils/routes";
import {
  formatStoryTime,
  hasStoryboard,
  hasTimeline,
  latestScript,
  storyDisplayText,
} from "./StoryProductionModel";
// prettier-ignore
import { CharacterChip, ReadyCell, StoryEnvironmentCoverage, StoryOutlineSection } from "./StoryProductionDetailParts";
import { useEpisodeGenerationAnchor } from "./useEpisodeGenerationAnchor";
import { StoryDetailEpisodeGeneration } from "./StoryDetailEpisodeGeneration";
export function StoryProductionDetail({ storyKey }: { storyKey: string }) {
  const { showAlert } = useAlertModal();
  const state = useStoryDetail({ storyKey, showAlert });
  const {
    story,
    episodes,
    scriptsByEpisode,
    timelinesByEpisode,
    loading,
    loadingScripts,
    setGenOpen,
    refresh,
    readiness,
    readinessLoading,
    readinessError,
    quickFixLoading,
    checkReadiness,
    runQuickFix,
    storyEnvironmentLinks,
  } = state;
  const openEpisodeGeneration = useEpisodeGenerationAnchor(setGenOpen);
  if (loading) {
    return <OperatorState title="加载故事详情..." />;
  }
  if (!story) {
    return <OperatorState title="故事不存在或无权访问。" tone="red" />;
  }

  const linkedCharacters = story.story_characters || story.characters || [];

  return (
    <OperatorWorkspace
      variant="main-inspector"
      main={
        <OperatorMainCanvas className="space-y-5">
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
              <div className="flex flex-wrap gap-2">
                {story.workflow_mode !== "novel_adaptation_v1" ? (
                  <button
                    type="button"
                    onClick={openEpisodeGeneration}
                    className={operatorButtonClass(
                      "primary",
                      "whitespace-nowrap",
                    )}
                  >
                    生成剧集
                  </button>
                ) : null}
                <button className={operatorButtonClass("secondary")}>
                  编辑故事
                </button>
              </div>
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
                  暂未关联 IP
                </span>
              )}
              <StoryEnvironmentCoverage links={storyEnvironmentLinks} />
            </div>
          </OperatorPanel>

          <StoryOutlineSection story={story} />
          {story.workflow_mode === "novel_adaptation_v1" ? (
            <StoryNovelWorkflowPanel
              story={story}
              onEpisodesApplied={refresh}
            />
          ) : (
            <>
              <StoryNovelExportPanel story={story} />
              <StoryDetailEpisodeGeneration state={state} />
            </>
          )}

          <OperatorPanel>
            <OperatorSectionHeader
              title="4. 剧集生产状态"
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
                    const script = latestScript(
                      scriptsByEpisode[episode.id] || [],
                    );
                    const timelineReady = hasTimeline(
                      episode,
                      script,
                      timelinesByEpisode[episode.id] || [],
                    );
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
                            className={operatorButtonClass(
                              "primary",
                              "whitespace-nowrap",
                            )}
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
        </OperatorMainCanvas>
      }
      inspector={
        <OperatorInspector title="生产控制" subtitle="就绪检查和生产准备">
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
        </OperatorInspector>
      }
    />
  );
}
