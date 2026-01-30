"use client";

import type { Script } from "@/utils/api";

interface ScriptListProps {
  scripts: Script[];
  formats: Array<{ value: string; label: string }>;
  languages: Array<{ value: string; label: string }>;
  onViewScript: (script: Script) => void;
  onRegenerateScript: (scriptId: number) => void;
  onDeleteScript: (scriptId: number) => void;
  onShowGenerateForm: () => void;
}

export function ScriptList({
  scripts,
  formats,
  languages,
  onViewScript,
  onRegenerateScript,
  onDeleteScript,
  onShowGenerateForm,
}: ScriptListProps) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">剧本列表</h2>
        <span className="text-sm text-gray-500">
          共 {scripts.length} 个剧本
        </span>
      </div>

      {scripts.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-gray-400 text-4xl mb-4">📝</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">暂无剧本</h3>
          <p className="text-gray-600 mb-4">开始生成您的第一个剧本吧！</p>
          <button
            onClick={onShowGenerateForm}
            className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
          >
            生成剧本
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {scripts.map((script) => (
            <div
              key={script.id}
              className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="font-medium text-gray-900">
                      {script.title}
                    </h3>
                    <span className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded-full">
                      {formats.find((f) => f.value === script.format_type)
                        ?.label || script.format_type}
                    </span>
                    <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                      {languages.find((l) => l.value === script.language)
                        ?.label || script.language}
                    </span>
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        script.status === "published"
                          ? "bg-green-100 text-green-800"
                          : script.status === "approved"
                          ? "bg-blue-100 text-blue-800"
                          : "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {script.status === "published"
                        ? "已发布"
                        : script.status === "approved"
                        ? "已批准"
                        : "草稿"}
                    </span>
                  </div>

                  <div className="flex items-center gap-4 text-xs text-gray-500 mb-2">
                    <span>字数: {script.word_count || 0}</span>
                    <span>字符: {script.character_count || 0}</span>
                    <span>页数: {script.page_count || 0}</span>
                    <span>版本: {script.version}</span>
                  </div>

                  <div className="text-xs text-gray-500">
                    创建: {new Date(script.created_at).toLocaleDateString()}
                  </div>
                </div>

                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => onViewScript(script)}
                    className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                  >
                    查看内容
                  </button>
                  <button
                    onClick={() => onRegenerateScript(script.id)}
                    className="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700"
                  >
                    重新生成
                  </button>
                  <button
                    onClick={() => onDeleteScript(script.id)}
                    className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                  >
                    删除
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
