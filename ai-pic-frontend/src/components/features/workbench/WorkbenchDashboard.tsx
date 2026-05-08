"use client";

import Link from "next/link";
import {
  OperatorShell,
  OperatorPanel,
  OperatorInspector,
  OperatorMainCanvas,
  OperatorSectionHeader,
  OperatorState,
  OperatorWorkspace,
  ProgressBar,
  StatusPill,
  operatorButtonClass,
  operatorTableClass,
  operatorTableHeadClass,
  operatorTableRowClass,
  taskStatusTone,
} from "@/components/shared";
import { useWorkbenchSummary } from "@/hooks/useWorkbenchSummary";
import type { WorkbenchTask } from "@/utils/api/types";
import { episodeWorkspaceHref } from "@/utils/routes";
import { AuditItem, MetricCard, ReadyCell } from "./WorkbenchDashboardParts";

const formatDateTime = (value: string) =>
  new Date(value).toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });

const taskStatusLabel = (status: string) => {
  if (status === "processing") return "生成中";
  if (status === "pending") return "排队中";
  if (status === "completed") return "已完成";
  if (status === "failed") return "失败";
  if (status === "cancelled") return "已取消";
  return status;
};

const taskTone = (task: WorkbenchTask) =>
  task.status === "failed"
    ? "red"
    : task.status === "completed"
    ? "green"
    : task.status === "processing"
    ? "amber"
    : "blue";

export function WorkbenchDashboard() {
  const { summary, loading, error, refresh } = useWorkbenchSummary();

  return (
    <OperatorShell
      title="IP 生产工作台"
      subtitle="以 IP 为中心继续故事、剧集和任务"
      breadcrumb={["IP 中心", "生产工作台"]}
    >
      {loading ? (
        <OperatorState title="加载工作台数据..." />
      ) : error ? (
        <OperatorState
          title={error}
          tone="red"
          action={
            <button
              type="button"
              onClick={() => void refresh()}
              className={operatorButtonClass("danger")}
            >
              重试
            </button>
          }
        />
      ) : summary ? (
        <OperatorWorkspace
          variant="main-inspector"
          main={
            <OperatorMainCanvas className="space-y-5">
            <OperatorPanel className="p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="text-sm font-semibold text-gray-950">
                    IP / 环境生产状态
                  </h2>
                  <p className="mt-1 text-xs text-gray-500">
                    当前生产围绕 IP、故事、剧集和环境资产推进；新内容优先从 IP 项目进入。
                  </p>
                </div>
                <Link href="/virtual-ip" className={operatorButtonClass("primary")}>
                  进入 IP 项目
                </Link>
              </div>
            </OperatorPanel>

            <div className="grid gap-3 md:grid-cols-4">
              <MetricCard label="今日待处理" value={summary.metrics.pending_tasks} />
              <MetricCard label="生成中" value={summary.metrics.running_tasks} />
              <MetricCard label="失败任务" value={summary.metrics.failed_tasks} tone="red" />
              <MetricCard
                label="可继续生产"
                value={summary.metrics.continuable_episodes}
                tone="green"
              />
            </div>

            <OperatorPanel>
              <OperatorSectionHeader
                title="继续制作"
                subtitle="从现有内容继续推进到剧集时间轴"
                action={
                  <Link href="/stories" className={operatorButtonClass("secondary")}>
                    查看全部
                  </Link>
                }
              />
              <div className="overflow-x-auto">
                <table className={`${operatorTableClass} min-w-[1080px]`}>
                  <thead className={operatorTableHeadClass}>
                    <tr>
                      <th className="w-[280px] px-5 py-3 text-left font-medium">
                        IP / 故事 / 剧集
                      </th>
                      <th className="px-4 py-3 text-left font-medium">当前阶段</th>
                      <th className="px-4 py-3 text-left font-medium">剧本</th>
                      <th className="px-4 py-3 text-left font-medium">时间轴</th>
                      <th className="px-4 py-3 text-left font-medium">分镜</th>
                      <th className="px-4 py-3 text-left font-medium">最后更新</th>
                      <th className="px-5 py-3 text-right font-medium">操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {summary.recent_episodes.map((episode) => (
                      <tr
                        key={episode.episode_id}
                        className={operatorTableRowClass}
                      >
                        <td className="w-[280px] px-5 py-4">
                          <div className="line-clamp-2 font-medium text-gray-950">
                            {episode.story_title}
                          </div>
                          <div className="mt-1 text-xs text-gray-500">
                            第{episode.episode_number}集 · {episode.episode_title}
                          </div>
                        </td>
                        <td className="px-4 py-4">
                          <StatusPill tone={episode.timeline_ready ? "green" : "blue"}>
                            {episode.current_stage_label}
                          </StatusPill>
                        </td>
                        <ReadyCell ready={episode.script_ready} />
                        <ReadyCell ready={episode.timeline_ready} />
                        <ReadyCell ready={episode.storyboard_ready} />
                        <td className="px-4 py-4 text-xs text-gray-500">
                          {formatDateTime(episode.updated_at)}
                        </td>
                        <td className="px-5 py-4 text-right">
                          <Link
                            href={episodeWorkspaceHref(episode.episode_business_id, {
                              tab: "timeline",
                              scriptId: episode.latest_script_id,
                            })}
                            className={operatorButtonClass("primary", "whitespace-nowrap")}
                          >
                            进入时间轴
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </OperatorPanel>
            </OperatorMainCanvas>
          }
          inspector={
            <OperatorInspector title="任务与审计">
              <div className="space-y-5">
                <div>
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <h2 className="text-sm font-semibold text-gray-950">任务队列</h2>
                    <Link href="/tasks" className={operatorButtonClass("ghost")}>
                      查看全部
                    </Link>
                  </div>
                  <div className="space-y-4">
                {summary.task_queue.map((task) => (
                  <div key={task.id} className="space-y-2">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="truncate text-sm font-medium text-gray-950">
                          {task.title}
                        </div>
                        <div className="mt-0.5 text-xs text-gray-500">
                          {task.task_type}
                        </div>
                      </div>
                      <StatusPill tone={taskStatusTone(task.status)}>
                        {taskStatusLabel(task.status)}
                      </StatusPill>
                    </div>
                    <ProgressBar value={task.progress} tone={taskTone(task)} />
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>{task.progress}%</span>
                      {task.status === "failed" ? (
                        <Link href="/tasks" className="font-medium text-red-600">
                          重试
                        </Link>
                      ) : (
                        <span>{formatDateTime(task.updated_at)}</span>
                      )}
                    </div>
                  </div>
                ))}
                  </div>
                </div>

                <div className="border-t border-gray-200 pt-4">
                  <h2 className="text-sm font-semibold">运行审计</h2>
                  <div className="mt-4 grid grid-cols-2 gap-3 text-xs text-gray-600">
                    <AuditItem label="脚本校验" value="通过" />
                    <AuditItem label="分镜校验" value="通过" />
                    <AuditItem label="时长校验" value="待复核" tone="amber" />
                    <AuditItem label="敏感内容" value="通过" />
                  </div>
                </div>
              </div>
            </OperatorInspector>
          }
        />
      ) : null}
    </OperatorShell>
  );
}
