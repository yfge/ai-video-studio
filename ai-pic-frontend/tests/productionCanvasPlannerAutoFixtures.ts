import {
  jsonResponse,
  parseRequestBody,
  skillNode,
  type FetchInit,
  type FetchInput,
  type PlannerFetchStub,
  type RequestPayload,
} from "./productionCanvasPlannerFetchCommon";

export function installAutoSkillFetch(): PlannerFetchStub {
  return installAutoPlannerFetch({
    executeRunId: "canvas-run-auto",
    planNodes: [
      skillNode({
        id: "skill-script-generate",
        label: "Script Skill",
        title: "现有剧本生成入口已就绪",
        status: "ready",
        x: 420,
        y: 360,
        skill: "script.generate",
        detail: "后台复用现有剧本生成队列。",
        outputs: { episode_id: 123 },
      }),
    ],
  });
}

export function installMediaPlannerFetch(): PlannerFetchStub {
  return installAutoPlannerFetch({
    executeRunId: "canvas-run-media",
    planNodes: [
      skillNode({
        id: "skill-image-candidates",
        label: "Image Candidates",
        title: "现有分镜图片候选入口已就绪",
        status: "ready",
        x: 420,
        y: 360,
        skill: "image.candidates",
        detail: "后台复用现有分镜图片生成队列。",
        outputs: { script_id: 321, frame_indexes: [1] },
      }),
      skillNode({
        id: "skill-video-candidates",
        label: "Video Candidates",
        title: "现有分镜视频候选入口已就绪",
        status: "ready",
        x: 700,
        y: 360,
        skill: "video.candidates",
        detail: "后台复用现有分镜视频生成队列。",
        outputs: { script_id: 321, frame_indexes: [1] },
      }),
    ],
  });
}

function installAutoPlannerFetch({
  executeRunId,
  planNodes,
}: {
  executeRunId: string;
  planNodes: RequestPayload[];
}): PlannerFetchStub {
  const originalFetch = globalThis.fetch;
  const executeRequests: RequestPayload[] = [];
  const planRequests: RequestPayload[] = [];
  const taskRequests: string[] = [];

  globalThis.fetch = async (input: FetchInput, init?: FetchInit) => {
    const url = String(input);
    if (url.includes("/production-canvas/execute")) {
      const executeRequest = parseRequestBody(init);
      executeRequests.push(executeRequest);
      const isImage = executeRequest.skill === "image.candidates";
      const isVideo = executeRequest.skill === "video.candidates";
      return jsonResponse({
        task_id: isImage ? 91 : isVideo ? 92 : 77,
        task_status: "pending",
        skill_result: skillNode({
          skill: executeRequest.skill,
          label: isImage
            ? "Image Candidates"
            : isVideo
            ? "Video Candidates"
            : "Script Skill",
          title: isImage
            ? "已提交现有分镜图片候选任务"
            : isVideo
            ? "已提交现有分镜视频候选任务"
            : "已提交现有剧本生成任务",
          status: "running",
          detail: "后台已通过现有 worker 执行。",
          outputs: {
            episode_id: 123,
            script_id: 321,
            dispatched_task_id: isImage ? 91 : isVideo ? 92 : 77,
            task_status: "pending",
            frame_indexes: isImage || isVideo ? [1] : undefined,
            canvas_run_id: executeRunId,
          },
        }),
      });
    }

    planRequests.push(parseRequestBody(init));
    return jsonResponse({
      run_id: executeRunId,
      task_id: 44,
      nodes: planNodes,
      selected_assets: { virtual_ips: [], environments: [] },
      skill_manifest: { version: "production_canvas.v1" },
    });
  };

  return {
    executeRequests,
    planRequests,
    taskRequests,
    restore: () => {
      globalThis.fetch = originalFetch;
    },
  };
}
