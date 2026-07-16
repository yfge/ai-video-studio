"use client";

import {
  OperatorPanel,
  OperatorPagination,
  OperatorSectionHeader,
  OperatorState,
  StatusPill,
  type OperatorPaginationModel,
  operatorButtonClass,
} from "@/components/shared";
import type { Environment } from "@/utils/api/types";
import { resolveCreatorLabel } from "@/utils/creator";

interface EnvironmentListProps {
  loading: boolean;
  list: Environment[];
  onRefresh: () => void;
  onManage: (env: Environment) => void;
  onDelete: (env: Environment) => void;
  pagination?: OperatorPaginationModel;
}

export function EnvironmentList({
  loading,
  list,
  onRefresh,
  onManage,
  onDelete,
  pagination,
}: EnvironmentListProps) {
  return (
    <OperatorPanel>
      <OperatorSectionHeader
        title="环境列表"
        subtitle={`${
          pagination?.total ?? list.length
        } 个环境资产 · 按 IP 项目复用的场景资产池`}
        action={
          <button
            type="button"
            onClick={onRefresh}
            className={operatorButtonClass("secondary")}
          >
            刷新
          </button>
        }
      />
      {loading ? (
        <div className="p-4">
          <OperatorState title="加载环境资产..." />
        </div>
      ) : list.length === 0 ? (
        <div className="p-4">
          <OperatorState
            title="暂无环境资产"
            detail="创建后可在详情内管理图片。"
          />
        </div>
      ) : (
        <>
          <div className="grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-3">
            {list.map((env) => (
              <article
                key={env.id}
                className="rounded-lg border border-gray-200 bg-white p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h3 className="truncate text-sm font-semibold text-gray-950">
                      {env.name}
                    </h3>
                    <p className="mt-1 text-xs text-gray-500">
                      {resolveCreatorLabel(env.creator)} ·{" "}
                      {new Date(env.created_at).toLocaleDateString("zh-CN")}
                    </p>
                  </div>
                  <StatusPill
                    tone={
                      (env.linked_virtual_ip_count || 0) > 0 ? "green" : "amber"
                    }
                  >
                    {(env.linked_virtual_ip_count || 0) > 0
                      ? `已接入 ${env.linked_virtual_ip_count} IP`
                      : "未关联 IP"}
                  </StatusPill>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => onManage(env)}
                      className={operatorButtonClass(
                        "ghost",
                        "whitespace-nowrap",
                      )}
                    >
                      管理图片
                    </button>
                    <button
                      type="button"
                      onClick={() => onDelete(env)}
                      className="h-8 rounded-md px-2 text-xs font-medium text-red-600 hover:bg-red-50 whitespace-nowrap"
                    >
                      删除
                    </button>
                  </div>
                </div>

                <div className="mt-3 text-xs text-gray-500">
                  类别：{env.category || "未指定"}
                </div>
                {env.tags && env.tags.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {env.tags.map((tag) => (
                      <span
                        key={tag}
                        className="rounded-md border border-gray-200 bg-gray-50 px-2 py-1 text-xs text-gray-600"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
                {env.linked_virtual_ips &&
                  env.linked_virtual_ips.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {env.linked_virtual_ips.slice(0, 3).map((ip) => (
                        <span
                          key={ip.id}
                          className="rounded-md border border-blue-100 bg-blue-50 px-2 py-1 text-xs text-blue-700"
                        >
                          IP: {ip.name}
                        </span>
                      ))}
                    </div>
                  )}
                {env.description && (
                  <p className="mt-3 line-clamp-3 text-sm leading-6 text-gray-600">
                    {env.description}
                  </p>
                )}
              </article>
            ))}
          </div>
          {pagination ? (
            <OperatorPagination {...pagination} itemLabel="环境资产" />
          ) : null}
        </>
      )}
    </OperatorPanel>
  );
}
