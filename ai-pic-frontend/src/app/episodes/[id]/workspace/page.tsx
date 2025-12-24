"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo, useState } from "react";

import {
  EpisodeWorkspaceHeader,
  type WorkflowStatus,
} from "@/components/features/episode/EpisodeWorkspaceHeader";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import { useEpisodeDetail } from "@/hooks/useEpisodeDetail";

type TabKey = "script" | "timeline" | "storyboard";

export default function EpisodeWorkspacePage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const episodeKey = params?.id?.toString() || "";
  const { showAlert } = useAlertModal();

  // Get initial tab from URL or default to "script"
  const initialTab = (searchParams.get("tab") as TabKey) || "script";
  const [activeTab, setActiveTab] = useState<TabKey>(initialTab);

  // Use the existing episode detail hook
  const { episode, scripts, loading } = useEpisodeDetail({ episodeKey, showAlert });

  // Get the first/main script
  const mainScript = scripts?.[0] ?? null;

  // Calculate workflow status based on data
  const workflowStatus: WorkflowStatus = useMemo(() => {
    const hasScript = scripts && scripts.length > 0;
    const episodeMeta = episode?.metadata as Record<string, unknown> | undefined;
    const extraMeta = episodeMeta?.extra_metadata as Record<string, unknown> | undefined;
    const hasTimeline = Boolean(extraMeta?.audio_timeline);
    const scriptMeta = mainScript?.metadata as Record<string, unknown> | undefined;
    const hasStoryboard = Boolean(scriptMeta?.storyboard);

    return {
      script: hasScript ? "ready" : "pending",
      timeline: hasTimeline ? "ready" : "pending",
      storyboard: hasStoryboard ? "ready" : "pending",
    };
  }, [episode, scripts, mainScript]);

  // Update URL when tab changes
  const handleTabChange = useCallback(
    (tab: TabKey) => {
      setActiveTab(tab);
      router.replace(`/episodes/${episodeKey}/workspace?tab=${tab}`, {
        scroll: false,
      });
    },
    [router, episodeKey]
  );

  // Navigation handlers
  const handleNavigateBack = useCallback(() => {
    const storyId = episode?.story_id;
    if (storyId) {
      router.push(`/stories/${storyId}`);
    } else {
      router.push("/stories");
    }
  }, [router, episode]);

  const handleGenerateScript = useCallback(() => {
    // Navigate to episode page with generate form open
    router.push(`/episodes/${episodeKey}?action=generate-script`);
  }, [router, episodeKey]);

  const handleGenerateTimeline = useCallback(() => {
    // Navigate to episode page timeline section
    router.push(`/episodes/${episodeKey}?action=generate-timeline`);
  }, [router, episodeKey]);

  const handleGenerateStoryboard = useCallback(() => {
    // Navigate to storyboard page
    router.push(`/episodes/${episodeKey}/storyboard`);
  }, [router, episodeKey]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  if (!loading && !episode) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-red-500">剧集不存在</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <EpisodeWorkspaceHeader
          episode={episode}
          script={mainScript}
          workflowStatus={workflowStatus}
          activeTab={activeTab}
          onTabChange={handleTabChange}
          onNavigateBack={handleNavigateBack}
          onGenerateScript={handleGenerateScript}
          onGenerateTimeline={handleGenerateTimeline}
          onGenerateStoryboard={handleGenerateStoryboard}
        />

        {/* Tab Content */}
        <div className="mt-6">
          {activeTab === "script" && (
            <ScriptTabContent
              episodeKey={episodeKey}
              script={mainScript}
              onGenerateScript={handleGenerateScript}
            />
          )}
          {activeTab === "timeline" && (
            <TimelineTabContent
              episodeKey={episodeKey}
              hasTimeline={workflowStatus.timeline === "ready"}
              onGenerateTimeline={handleGenerateTimeline}
            />
          )}
          {activeTab === "storyboard" && (
            <StoryboardTabContent
              episodeKey={episodeKey}
              hasStoryboard={workflowStatus.storyboard === "ready"}
              onGoToStoryboard={handleGenerateStoryboard}
            />
          )}
        </div>
      </div>
    </div>
  );
}

// Placeholder components for tab content
// These will be enhanced in Phase 4

interface ScriptTabContentProps {
  episodeKey: string;
  script: unknown;
  onGenerateScript: () => void;
}

function ScriptTabContent({ script, onGenerateScript }: ScriptTabContentProps) {
  const router = useRouter();

  if (!script) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <h3 className="text-lg font-medium text-gray-900 mb-2">暂无剧本</h3>
        <p className="text-gray-500 mb-4">请先生成剧本以继续工作流</p>
        <button
          onClick={onGenerateScript}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          生成剧本
        </button>
      </div>
    );
  }

  const scriptData = script as { business_id?: string };
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">剧本内容</h3>
        <button
          onClick={() => router.push(`/scripts/${scriptData.business_id}`)}
          className="text-blue-600 hover:text-blue-700 text-sm"
        >
          查看完整剧本 →
        </button>
      </div>
      <p className="text-gray-500 text-sm">
        剧本已生成。点击上方按钮查看完整内容和场景详情。
      </p>
    </div>
  );
}

interface TimelineTabContentProps {
  episodeKey: string;
  hasTimeline: boolean;
  onGenerateTimeline: () => void;
}

function TimelineTabContent({
  episodeKey,
  hasTimeline,
  onGenerateTimeline,
}: TimelineTabContentProps) {
  const router = useRouter();

  if (!hasTimeline) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <h3 className="text-lg font-medium text-gray-900 mb-2">暂无时间轴</h3>
        <p className="text-gray-500 mb-4">请先生成对白音轨和时间轴数据</p>
        <button
          onClick={onGenerateTimeline}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700"
        >
          生成时间轴
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">时间轴数据</h3>
        <button
          onClick={() => router.push(`/episodes/${episodeKey}`)}
          className="text-indigo-600 hover:text-indigo-700 text-sm"
        >
          查看完整时间轴 →
        </button>
      </div>
      <p className="text-gray-500 text-sm">
        时间轴已生成。点击上方按钮查看对白音轨和时间分布详情。
      </p>
    </div>
  );
}

interface StoryboardTabContentProps {
  episodeKey: string;
  hasStoryboard: boolean;
  onGoToStoryboard: () => void;
}

function StoryboardTabContent({
  hasStoryboard,
  onGoToStoryboard,
}: StoryboardTabContentProps) {
  if (!hasStoryboard) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <h3 className="text-lg font-medium text-gray-900 mb-2">暂无分镜</h3>
        <p className="text-gray-500 mb-4">请先生成分镜帧占位</p>
        <button
          onClick={onGoToStoryboard}
          className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
        >
          前往分镜管理
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">分镜内容</h3>
        <button
          onClick={onGoToStoryboard}
          className="text-purple-600 hover:text-purple-700 text-sm"
        >
          进入分镜管理 →
        </button>
      </div>
      <p className="text-gray-500 text-sm">
        分镜已生成。点击上方按钮管理分镜帧、生成图像和视频。
      </p>
    </div>
  );
}
