import { timelineAPI } from "@/utils/api/endpoints";
import type {
  ApiResponse,
  TimelineClipVideoReworkTaskRequest,
  TimelineClipVideoReworkTaskResponse,
  TimelineResponse,
} from "@/utils/api/types";

export async function queueTimelineClipVideoReworkWithVersionRefresh({
  timelineId,
  clipId,
  payload,
  onTimelineRefreshed,
}: {
  timelineId: number | string;
  clipId: string;
  payload: TimelineClipVideoReworkTaskRequest;
  onTimelineRefreshed?: (timeline: TimelineResponse) => void | Promise<void>;
}): Promise<ApiResponse<TimelineClipVideoReworkTaskResponse>> {
  const first = await timelineAPI.queueTimelineClipVideoRework(
    timelineId,
    clipId,
    payload,
  );
  if (first.status !== 409) return first;

  const latest = await timelineAPI.getTimeline(timelineId);
  if (!latest.success || !latest.data) {
    return {
      ...first,
      error: "Timeline 已更新，刷新失败，请重新加载后再试",
    };
  }

  await onTimelineRefreshed?.(latest.data);
  return {
    ...first,
    error:
      "Timeline 已更新，已刷新；本次未提交视频生成任务，不会产生生成费用。请重新复核后再生成。",
  };
}
