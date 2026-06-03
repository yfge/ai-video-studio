import type { StoryboardSupportFrame } from "./WorkspaceStoryboardSupportModel";

export function StoryboardSupportFrameRow({
  frame,
}: {
  frame: StoryboardSupportFrame;
}) {
  return (
    <div className="grid gap-3 px-4 py-3 text-xs text-gray-600 lg:grid-cols-[120px_minmax(0,1fr)_180px]">
      <div>
        <div className="font-semibold text-gray-950">
          #{frame.frameNumber} · {frame.timeLabel}
        </div>
        <div className="mt-1 text-gray-500">
          {frame.beatType ?? "beat"} · {frame.status}
        </div>
      </div>
      <div className="min-w-0">
        <div className="font-medium text-gray-900">{frame.description}</div>
        <div className="mt-1 truncate text-gray-500">
          {frame.sceneLabel ?? frame.sceneNumber ?? "未关联场景"}
        </div>
        <div className="mt-2 line-clamp-2 text-gray-600">
          {frame.promptDescription ?? frame.aiPrompt ?? "暂无镜头提示"}
        </div>
        {frame.clipId ? (
          <div className="mt-2 font-mono text-[11px] text-gray-500">
            {frame.clipId}
            {frame.gridPanelIndex ? ` · Panel ${frame.gridPanelIndex}` : ""}
          </div>
        ) : null}
      </div>
      <div className="flex flex-col gap-2">
        <AssetLink label="关键帧" url={frame.imageUrl} />
        <AssetLink label="视频" url={frame.videoUrl} />
        <div className="text-gray-500">
          来源：{frame.sourceKind ?? "storyboard"}
        </div>
        {frame.speakerName ? (
          <div className="text-gray-500">角色：{frame.speakerName}</div>
        ) : null}
      </div>
    </div>
  );
}

function AssetLink({ label, url }: { label: string; url: string | null }) {
  if (!url) {
    return <span className="text-gray-400">{label}: 未生成</span>;
  }
  return (
    <a
      href={url}
      target="_blank"
      rel="noreferrer"
      className="truncate font-medium text-blue-700 hover:text-blue-900"
    >
      {label}: 已关联
    </a>
  );
}
