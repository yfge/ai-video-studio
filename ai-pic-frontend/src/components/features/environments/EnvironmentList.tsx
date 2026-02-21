"use client";

import type { Environment } from "@/utils/api/types";
import { resolveCreatorLabel } from "@/utils/creator";

interface EnvironmentListProps {
  loading: boolean;
  list: Environment[];
  onRefresh: () => void;
  onManage: (env: Environment) => void;
  onDelete: (env: Environment) => void;
}

export function EnvironmentList({
  loading,
  list,
  onRefresh,
  onManage,
  onDelete,
}: EnvironmentListProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">环境列表</h2>
        <button
          onClick={onRefresh}
          className="text-blue-600 hover:text-blue-800 text-sm"
        >
          刷新
        </button>
      </div>
      {loading ? (
        <div className="py-8 text-center text-gray-500">加载中...</div>
      ) : list.length === 0 ? (
        <div className="py-8 text-center text-gray-500">
          暂无环境，请先创建。
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {list.map((env) => (
            <div
              key={env.id}
              className="border rounded p-4 hover:shadow-sm space-y-3"
            >
              <div className="text-xs text-gray-500">
                创建者：{resolveCreatorLabel(env.creator)}
              </div>
              <div className="flex items-center justify-between mb-2">
                <div className="font-semibold text-gray-900">{env.name}</div>
                <div className="flex gap-2">
                  <button
                    onClick={() => onManage(env)}
                    className="text-blue-600 hover:text-blue-800 text-xs"
                  >
                    管理图片
                  </button>
                  <button
                    onClick={() => onDelete(env)}
                    className="text-red-600 hover:text-red-800 text-xs"
                  >
                    删除
                  </button>
                </div>
              </div>
              <div className="text-xs text-gray-500 mb-2">
                类别：{env.category || "未指定"}
              </div>
              {env.tags && env.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-2">
                  {env.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-xs"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
              {env.description && (
                <p className="text-sm text-gray-700 line-clamp-3 mb-2">
                  {env.description}
                </p>
              )}
              <div className="text-xs text-gray-400 mt-1">
                创建于 {new Date(env.created_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
