"use client";

import type { Script } from "@/utils/api/types";
import {
  OperatorPanel,
  OperatorSectionHeader,
  OperatorState,
  StatusPill,
  operatorButtonClass,
} from "@/components/shared";

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
    <OperatorPanel>
      <OperatorSectionHeader
        title="剧本列表"
        subtitle={`共 ${scripts.length} 个剧本`}
        action={
          <button
            type="button"
            onClick={onShowGenerateForm}
            className={operatorButtonClass("primary")}
          >
            生成剧本
          </button>
        }
      />
      {scripts.length === 0 ? (
        <div className="p-4">
          <OperatorState title="暂无剧本" detail="开始生成本集第一个剧本。" />
        </div>
      ) : (
        <div className="divide-y divide-gray-100">
          {scripts.map((script) => (
            <div key={script.id} className="px-4 py-3 hover:bg-gray-50">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <h3 className="font-medium text-gray-900">{script.title}</h3>
                    <StatusPill tone="gray">
                      {formats.find((f) => f.value === script.format_type)?.label ||
                        script.format_type}
                    </StatusPill>
                    <StatusPill tone="blue">
                      {languages.find((l) => l.value === script.language)?.label ||
                        script.language}
                    </StatusPill>
                    <StatusPill tone={script.status === "published" ? "green" : "gray"}>
                      {script.status === "published"
                        ? "已发布"
                        : script.status === "approved"
                        ? "已批准"
                        : "草稿"}
                    </StatusPill>
                  </div>
                  <div className="mb-2 flex flex-wrap items-center gap-4 text-xs text-gray-500">
                    <span>字数: {script.word_count || 0}</span>
                    <span>字符: {script.character_count || 0}</span>
                    <span>页数: {script.page_count || 0}</span>
                    <span>版本: {script.version}</span>
                  </div>
                  <div className="text-xs text-gray-500">
                    创建: {new Date(script.created_at).toLocaleDateString()}
                  </div>
                </div>
                <div className="ml-4 flex shrink-0 gap-2">
                  <button
                    type="button"
                    onClick={() => onViewScript(script)}
                    className={operatorButtonClass("primary")}
                  >
                    查看内容
                  </button>
                  <button
                    type="button"
                    onClick={() => onRegenerateScript(script.id)}
                    className={operatorButtonClass("secondary")}
                  >
                    重新生成
                  </button>
                  <button
                    type="button"
                    onClick={() => onDeleteScript(script.id)}
                    className={operatorButtonClass("ghost", "text-red-700")}
                  >
                    删除
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </OperatorPanel>
  );
}
