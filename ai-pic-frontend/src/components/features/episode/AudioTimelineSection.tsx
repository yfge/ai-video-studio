"use client";

import { useMemo } from "react";
import type { NormalizedScene, Script, Task } from "@/utils/api";
import { Timeline, type TimelineTrack } from "@/components/features";
import { asRecord, getString, getNumber, parseMs } from "@/hooks/useEpisodeDetail";

interface AudioTimelineSectionProps {
  scripts: Script[];
  selectedScriptId: number | null;
  selectedScript: Script | null;
  onSelectScript: (id: number | null) => void;
  episodeMeta: Record<string, unknown>;
  selectedAudioTimeline: Record<string, unknown> | null;
  selectedStoryboard: Record<string, unknown> | null;
  normalizedScenes: NormalizedScene[];
  normalizedScenesLoading: boolean;
  normalizedScenesError: string | null;

  // Tasks
  sceneAudioTaskId: number | null;
  timelineTaskId: number | null;
  storyboardTaskId: number | null;
  sceneAudioTask: Task | null;
  timelineTask: Task | null;
  storyboardTask: Task | null;

  // Busy states
  sceneAudioBusy: boolean;
  timelineBusy: boolean;
  storyboardBusy: boolean;

  // Overwrite options
  overwriteSceneAudio: boolean;
  setOverwriteSceneAudio: (value: boolean) => void;
  overwriteTimeline: boolean;
  setOverwriteTimeline: (value: boolean) => void;
  overwriteStoryboard: boolean;
  setOverwriteStoryboard: (value: boolean) => void;
  minPauseSeconds: number;
  setMinPauseSeconds: (value: number) => void;

  // Actions
  onGenerateSceneDialogueAudio: () => void;
  onGenerateAudioTimeline: () => void;
  onGenerateStoryboardFromAudioTimeline: () => void;
  onNavigateToTasks: () => void;
  onNavigateToScript: () => void;
}

export function AudioTimelineSection({
  scripts,
  selectedScriptId,
  selectedScript,
  onSelectScript,
  selectedAudioTimeline,
  selectedStoryboard,
  normalizedScenes,
  normalizedScenesLoading,
  normalizedScenesError,
  sceneAudioTaskId,
  timelineTaskId,
  storyboardTaskId,
  sceneAudioTask,
  timelineTask,
  storyboardTask,
  sceneAudioBusy,
  timelineBusy,
  storyboardBusy,
  overwriteSceneAudio,
  setOverwriteSceneAudio,
  overwriteTimeline,
  setOverwriteTimeline,
  overwriteStoryboard,
  setOverwriteStoryboard,
  minPauseSeconds,
  setMinPauseSeconds,
  onGenerateSceneDialogueAudio,
  onGenerateAudioTimeline,
  onGenerateStoryboardFromAudioTimeline,
  onNavigateToTasks,
  onNavigateToScript,
}: AudioTimelineSectionProps) {
  const selectedEpisodeAudio = asRecord(selectedAudioTimeline?.["episode_audio"]);
  const selectedEpisodeAudioUrl = getString(selectedEpisodeAudio?.["oss_url"]);
  const selectedEpisodeAudioVersion = selectedEpisodeAudio?.["version"];
  const selectedTimelineBeatCount = Array.isArray(selectedAudioTimeline?.["beats"])
    ? (selectedAudioTimeline?.["beats"] as unknown[]).length
    : 0;

  const selectedStoryboardFrames = useMemo(
    () =>
      Array.isArray(selectedStoryboard?.["frames"])
        ? (selectedStoryboard?.["frames"] as unknown[])
        : [],
    [selectedStoryboard],
  );
  const selectedStoryboardMeta = asRecord(selectedStoryboard?.["meta"]);
  const selectedStoryboardSource = getString(selectedStoryboardMeta?.["generation_source"]);

  const normalizedSceneAudio = normalizedScenes.map((scene) => {
    const meta = asRecord(scene.metadata);
    const payload = meta ? asRecord(meta["dialogue_audio"]) : null;
    const ossUrl = payload ? getString(payload["oss_url"]) : undefined;
    return {
      scene,
      ossUrl,
      version: payload ? payload["version"] : undefined,
      durationSeconds: payload ? payload["duration_seconds"] : undefined,
    };
  });
  const normalizedSceneAudioCount = normalizedSceneAudio.filter((item) =>
    Boolean(item.ossUrl),
  ).length;

  const pipelineSteps = [
    { key: "dialogue_audio", label: "生成对白音轨", done: normalizedSceneAudioCount > 0 },
    { key: "audio_timeline", label: "生成时间轴", done: Boolean(selectedAudioTimeline) },
    { key: "storyboard_slots", label: "生成分镜帧占位", done: Boolean(selectedStoryboard) },
  ];

  const pillClass = (done: boolean) =>
    `inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${
      done
        ? "bg-green-50 text-green-700 border border-green-200"
        : "bg-gray-50 text-gray-600 border border-gray-200"
    }`;

  const taskStatusText = (status: Task["status"] | undefined) => {
    switch (status) {
      case "pending":
        return "等待中";
      case "processing":
        return "进行中";
      case "completed":
        return "已完成";
      case "failed":
        return "失败";
      default:
        return "—";
    }
  };

  const timelineTracks = useMemo<TimelineTrack[]>(() => {
    const tracks: TimelineTrack[] = [];
    const beatsRaw = Array.isArray(selectedAudioTimeline?.["beats"])
      ? (selectedAudioTimeline?.["beats"] as unknown[])
      : [];
    const beatItems = beatsRaw
      .map<TimelineTrack["items"][number] | null>((raw, idx) => {
        const record =
          raw && typeof raw === "object" ? (raw as Record<string, unknown>) : null;
        if (!record) return null;
        const start = parseMs(record["start_ms"]);
        const end = parseMs(record["end_ms"]);
        if (start == null || end == null || end < start) return null;
        const text =
          getString(record["dialogue_excerpt"]) ??
          getString(record["text"]) ??
          getString(record["beat_summary"]);
        return {
          id: `beat-${idx}-${start}`,
          startMs: start,
          endMs: end,
          label: text || `Beat ${idx + 1}`,
          type: getString(record["beat_type"]) ?? undefined,
          color: "#2563eb",
        };
      })
      .filter((item): item is TimelineTrack["items"][number] => Boolean(item));
    if (beatItems.length > 0) {
      tracks.push({ id: "dialogue-beats", label: "对白 beats", color: "#2563eb", items: beatItems });
    }
    const storyboardItems = selectedStoryboardFrames
      .map<TimelineTrack["items"][number] | null>((fr, idx) => {
        const record = fr && typeof fr === "object" ? (fr as Record<string, unknown>) : null;
        if (!record) return null;
        const start = parseMs(record["start_ms"]);
        const end = parseMs(record["end_ms"]);
        if (start == null || end == null || end < start) return null;
        const frameNumber = getNumber(record["frame_number"]);
        const label = getString(record["description"]) || `Frame ${frameNumber ?? idx + 1}`;
        const rawId = record["frame_id"] ?? record["id"] ?? idx;
        const id = typeof rawId === "string" ? rawId : String(rawId);
        return { id: `frame-${id}`, startMs: start, endMs: end, label, type: "frame", color: "#a855f7" };
      })
      .filter((item): item is TimelineTrack["items"][number] => Boolean(item));
    if (storyboardItems.length > 0) {
      tracks.push({ id: "storyboard-frames", label: "分镜帧", color: "#a855f7", items: storyboardItems });
    }
    return tracks;
  }, [selectedAudioTimeline, selectedStoryboardFrames]);

  const timelineRange = useMemo(() => {
    if (timelineTracks.length === 0) return null;
    let min = Number.POSITIVE_INFINITY;
    let max = Number.NEGATIVE_INFINITY;
    timelineTracks.forEach((track) => {
      track.items.forEach((item) => {
        min = Math.min(min, item.startMs);
        max = Math.max(max, item.endMs);
      });
    });
    if (!Number.isFinite(min) || !Number.isFinite(max)) return null;
    return { startMs: min, endMs: max };
  }, [timelineTracks]);

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-4">
        <div>
          <h2 className="text-xl font-semibold">对白音轨与时间轴</h2>
          <p className="text-xs text-gray-500 mt-1">
            声音优先定时长（scene → audio → beats → timeline → storyboard）
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-gray-700">
            {pipelineSteps.map((step, idx) => (
              <div key={step.key} className="flex items-center gap-2">
                <span className={pillClass(step.done)}>
                  {step.done ? "✓" : "·"} {step.label}
                </span>
                {idx < pipelineSteps.length - 1 && <span className="text-gray-400">→</span>}
              </div>
            ))}
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onNavigateToTasks}
            className="bg-gray-100 text-gray-800 px-3 py-2 rounded-lg hover:bg-gray-200"
          >
            任务页
          </button>
          {selectedScript && (
            <button
              onClick={onNavigateToScript}
              className="bg-gray-100 text-gray-800 px-3 py-2 rounded-lg hover:bg-gray-200"
            >
              查看剧本
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">当前剧本</label>
          <select
            value={selectedScriptId ?? ""}
            onChange={(e) => {
              const next = Number(e.target.value);
              onSelectScript(Number.isFinite(next) ? next : null);
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="" disabled>请选择剧本</option>
            {scripts.map((script) => (
              <option key={script.id} value={script.id}>
                {script.title} (id={script.id})
              </option>
            ))}
          </select>
        </div>
        <div className="text-xs text-gray-600">
          <div className="mb-1">
            时间轴（episode）：{" "}
            {selectedAudioTimeline ? (
              <span>beats={selectedTimelineBeatCount} • version={String(selectedEpisodeAudioVersion ?? "—")}</span>
            ) : (
              <span className="text-gray-400">未生成</span>
            )}
          </div>
          <div className="mb-1">
            Episode 音频：{" "}
            {selectedEpisodeAudioUrl ? (
              <div className="mt-1">
                <a href={selectedEpisodeAudioUrl} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline break-all">
                  {selectedEpisodeAudioUrl}
                </a>
                <audio className="mt-2 w-full" controls preload="none" src={selectedEpisodeAudioUrl} />
              </div>
            ) : (
              <span className="text-gray-400">—</span>
            )}
          </div>
          <div>
            分镜占位（script）：{" "}
            {selectedStoryboard ? (
              <span>frames={selectedStoryboardFrames.length} • source={selectedStoryboardSource || "—"}</span>
            ) : (
              <span className="text-gray-400">—</span>
            )}
          </div>
        </div>
      </div>

      {/* Scene dialogue audio details */}
      <details open={normalizedSceneAudioCount > 0} className="rounded border border-gray-200 bg-gray-50 p-3 text-xs text-gray-700">
        <summary className="cursor-pointer select-none text-sm font-medium text-gray-800">
          场景对白音轨（scene）{normalizedScenes.length > 0 ? `：${normalizedSceneAudioCount}/${normalizedScenes.length} 已生成` : ""}
        </summary>
        <div className="mt-2 text-[11px] text-gray-600">每个场景一条混音音轨，来源于 scene.metadata.dialogue_audio.oss_url</div>
        {!normalizedScenesLoading && !normalizedScenesError && normalizedScenes.length === 0 && (
          <div className="mt-2 text-gray-500">暂无场景数据（请先选择剧本并完成「生成对白音轨」）</div>
        )}
        {normalizedScenesLoading && <div className="mt-2 text-gray-500">加载中...</div>}
        {normalizedScenesError && <div className="mt-2 text-red-600">{normalizedScenesError}</div>}
        {!normalizedScenesLoading && !normalizedScenesError && normalizedSceneAudio.length > 0 && (
          <div className="mt-3 space-y-2">
            {normalizedSceneAudio.map((item) => (
              <div key={item.scene.id} className="rounded border border-gray-200 bg-white p-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="text-xs font-medium text-gray-900 truncate">
                      Scene {item.scene.scene_number}: {item.scene.slug_line}
                    </div>
                    <div className="mt-0.5 text-[11px] text-gray-500">
                      id={item.scene.id}
                      {item.version != null ? ` • version=${String(item.version)}` : ""}
                      {item.durationSeconds != null ? ` • duration=${String(item.durationSeconds)}s` : ""}
                    </div>
                  </div>
                  {item.ossUrl ? (
                    <a href={item.ossUrl} target="_blank" rel="noreferrer" className="shrink-0 text-[11px] text-blue-600 hover:underline">打开</a>
                  ) : (
                    <span className="shrink-0 text-[11px] text-gray-400">未生成</span>
                  )}
                </div>
                {item.ossUrl && <audio className="mt-2 w-full" controls preload="none" src={item.ossUrl} />}
              </div>
            ))}
          </div>
        )}
      </details>

      <div className="flex flex-wrap gap-2 mb-3 mt-4">
        <button onClick={onGenerateSceneDialogueAudio} disabled={sceneAudioBusy || !selectedScriptId} className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50">
          {sceneAudioBusy ? "生成中..." : "生成对白音轨"}
        </button>
        <button onClick={onGenerateAudioTimeline} disabled={timelineBusy || !selectedScriptId} className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50">
          {timelineBusy ? "生成中..." : "生成时间轴"}
        </button>
        <button onClick={onGenerateStoryboardFromAudioTimeline} disabled={storyboardBusy || !selectedScriptId} className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50">
          {storyboardBusy ? "生成中..." : "生成分镜帧占位"}
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={overwriteSceneAudio} onChange={(e) => setOverwriteSceneAudio(e.target.checked)} />
          覆盖对白音轨
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={overwriteTimeline} onChange={(e) => setOverwriteTimeline(e.target.checked)} />
          覆盖时间轴
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={overwriteStoryboard} onChange={(e) => setOverwriteStoryboard(e.target.checked)} />
          覆盖分镜
        </label>
        <label className="flex items-center gap-2">
          pause阈值(s)
          <input
            type="number"
            step="0.1"
            min="0"
            max="10"
            value={minPauseSeconds}
            onChange={(e) => {
              const v = Number.parseFloat(e.target.value);
              setMinPauseSeconds(Number.isFinite(v) ? v : 1.5);
            }}
            className="w-20 px-2 py-1 border border-gray-300 rounded"
          />
        </label>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        <div className="border rounded p-3 bg-gray-50">
          <div className="text-sm font-medium text-gray-900">对白音轨任务</div>
          <div className="text-xs text-gray-600 mt-1">
            task_id: {sceneAudioTaskId ?? "—"} • 状态: {taskStatusText(sceneAudioTask?.status)}
          </div>
          {sceneAudioTask?.progress_detail && <div className="text-xs text-gray-600 mt-1 whitespace-pre-wrap">{sceneAudioTask.progress_detail}</div>}
        </div>
        <div className="border rounded p-3 bg-gray-50">
          <div className="text-sm font-medium text-gray-900">时间轴任务</div>
          <div className="text-xs text-gray-600 mt-1">
            task_id: {timelineTaskId ?? "—"} • 状态: {taskStatusText(timelineTask?.status)}
          </div>
          {timelineTask?.progress_detail && <div className="text-xs text-gray-600 mt-1 whitespace-pre-wrap">{timelineTask.progress_detail}</div>}
        </div>
        <div className="border rounded p-3 bg-gray-50">
          <div className="text-sm font-medium text-gray-900">分镜占位任务</div>
          <div className="text-xs text-gray-600 mt-1">
            task_id: {storyboardTaskId ?? "—"} • 状态: {taskStatusText(storyboardTask?.status)}
          </div>
          {storyboardTask?.progress_detail && <div className="text-xs text-gray-600 mt-1 whitespace-pre-wrap">{storyboardTask.progress_detail}</div>}
        </div>
      </div>

      <div className="mt-4">
        {timelineTracks.length === 0 ? (
          <div className="rounded border border-dashed border-gray-200 bg-gray-50 p-4 text-xs text-gray-600">
            生成时间轴后可视化对白 beats / 分镜帧的时间分布；分镜帧需携带 start/end_ms 才能显示。
          </div>
        ) : (
          <Timeline tracks={timelineTracks} startMs={timelineRange?.startMs} endMs={timelineRange?.endMs} initialZoom={1} />
        )}
      </div>
    </div>
  );
}
