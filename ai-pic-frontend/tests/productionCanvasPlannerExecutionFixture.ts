import {
  jsonResponse,
  parseRequestBody,
  reuseTarget,
  skillNode,
  taskData,
  type FetchInit,
  type FetchInput,
  type PlannerFetchStub,
  type RequestPayload,
} from "./productionCanvasPlannerFetchCommon";

export function installCanvasPlanExecutionFetch(): PlannerFetchStub {
  const originalFetch = globalThis.fetch;
  const executeRequests: RequestPayload[] = [];
  const planRequests: RequestPayload[] = [];
  const taskRequests: string[] = [];

  globalThis.fetch = async (input: FetchInput, init?: FetchInit) => {
    const url = String(input);
    if (url.includes("/api/v1/episodes?")) {
      return jsonResponse([
        { id: 123, episode_number: 4, title: "办公室轻喜剧" },
      ]);
    }
    if (
      url.includes("/api/v1/virtual-ips/") ||
      url.includes("/api/v1/story-structure/environments")
    ) {
      return jsonResponse([]);
    }
    if (url.includes("/api/v1/scripts?")) return jsonResponse([]);
    if (url.includes("/api/v1/tasks/77")) {
      taskRequests.push(url);
      return jsonResponse(
        taskData({
          id: 77,
          title: "剧本生成已完成",
          taskType: "script_generation",
          status: "completed",
          progress: "100%",
          updatedAt: "2026-07-02T00:03:00Z",
        }),
      );
    }
    if (url.includes("/api/v1/tasks/88")) {
      taskRequests.push(url);
      return jsonResponse(
        taskData({
          id: 88,
          title: "分镜生成失败",
          taskType: "storyboard_generation",
          status: "failed",
          progress: "80%",
          errorMessage: "缺少分镜输入",
          updatedAt: "2026-07-02T00:06:00Z",
        }),
      );
    }
    if (url.includes("/api/v1/tasks/44")) {
      taskRequests.push(url);
      return jsonResponse(
        taskData({
          id: 44,
          title: "生产画布整体创建",
          taskType: "text_generation",
          status: "completed",
          progress: "100%",
          updatedAt: "2026-07-02T00:07:00Z",
        }),
      );
    }
    if (url.includes("/production-canvas/execute")) {
      const executeRequest = parseRequestBody(init);
      executeRequests.push(executeRequest);
      return jsonResponse(executedSkillResult(executeRequest));
    }

    planRequests.push(parseRequestBody(init));
    return jsonResponse({
      run_id: "canvas-run-123",
      task_id: 44,
      nodes: planExecutionNodes(),
      selected_assets: {
        virtual_ips: [{ id: 1, name: "林妹妹" }],
        environments: [{ id: 2, name: "共享办公区" }],
      },
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

function executedSkillResult(executeRequest: RequestPayload) {
  if (executeRequest.skill === "report.summarize") {
    return {
      task_id: 44,
      task_status: "completed",
      skill_result: skillNode({
        skill: "report.summarize",
        label: "Report Skill",
        title: "已汇总现有任务证据",
        status: "review",
        detail:
          "任务 #44《生产画布整体创建》当前状态 completed；可继续在任务页检查参数。",
        outputs: {
          task_id: 44,
          task_type: "text_generation",
          task_status: "completed",
          source_kind: "production_canvas_run",
          canvas_run_id: "canvas-run-123",
        },
        reuse_targets: [
          reuseTarget(
            "api",
            "Task audit endpoint",
            "app.api.v1.endpoints.tasks",
          ),
        ],
      }),
    };
  }
  if (executeRequest.skill === "storyboard.plan") {
    return {
      task_id: 88,
      task_status: "pending",
      skill_result: skillNode({
        skill: "storyboard.plan",
        label: "Storyboard Skill",
        title: "已提交现有分镜生成任务",
        status: "running",
        detail: "后台已通过现有 STORYBOARD_GENERATION Celery worker 执行。",
        outputs: {
          script_id: 321,
          dispatched_task_id: 88,
          task_status: "pending",
          canvas_run_id: "canvas-run-123",
        },
        reuse_targets: [
          reuseTarget(
            "worker",
            "Storyboard Celery worker",
            "app.services.task_worker.storyboard_generate_task",
          ),
        ],
      }),
    };
  }
  return {
    task_id: 77,
    task_status: "pending",
    skill_result: skillNode({
      skill: "script.generate",
      label: "Script Skill",
      title: "已提交现有剧本生成任务",
      status: "running",
      detail: "后台已通过现有 SCRIPT_GENERATION Celery worker 执行。",
      outputs: {
        episode_id: 123,
        script_id: 321,
        dispatched_task_id: 77,
        task_status: "pending",
        canvas_run_id: "canvas-run-123",
      },
      reuse_targets: [
        reuseTarget(
          "worker",
          "Script Celery worker",
          "app.services.task_worker.script_generate_task",
        ),
      ],
    }),
  };
}

function planExecutionNodes() {
  return [
    skillNode({
      id: "skill-assets",
      label: "Asset Selection",
      title: "已选择林妹妹和共享办公区",
      status: "review",
      x: 160,
      y: 360,
      skill: "asset.select",
      detail: "复用现有 IP：林妹妹；环境：共享办公区",
      outputs: {
        virtual_ip_ids: [1],
        environment_ids: [2],
        candidate_environment_ids: [2],
      },
      reuse_targets: [
        reuseTarget(
          "repository",
          "Environment repository",
          "app.repositories.environment_repository.EnvironmentRepository",
        ),
      ],
    }),
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
      reuse_targets: [
        reuseTarget(
          "api",
          "Script async endpoint",
          "app.api.v1.endpoints.scripts_generation_queue.generate_script_async",
        ),
      ],
    }),
    skillNode({
      id: "skill-storyboard-plan",
      label: "Storyboard Skill",
      title: "现有分镜生成入口已就绪",
      status: "ready",
      x: 680,
      y: 360,
      skill: "storyboard.plan",
      detail: "需要先补齐执行上下文，之后才会调用现有生成 worker。",
      outputs: { required_inputs: ["script_id"] },
      reuse_targets: [
        reuseTarget(
          "worker",
          "Storyboard task processor",
          "app.api.v1.endpoints.storyboard.task_processors._process_storyboard_generation_task",
        ),
      ],
    }),
    skillNode({
      id: "skill-report-summarize",
      label: "Report Skill",
      title: "等待汇总画布执行证据",
      status: "blocked",
      x: 960,
      y: 360,
      skill: "report.summarize",
      detail: "需要 task_id 后汇总任务证据。",
      outputs: { required_inputs: ["task_id"] },
      reuse_targets: [
        reuseTarget("api", "Task audit endpoint", "app.api.v1.endpoints.tasks"),
      ],
    }),
  ];
}
