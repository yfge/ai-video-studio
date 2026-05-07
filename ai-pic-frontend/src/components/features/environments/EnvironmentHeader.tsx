"use client";

import { operatorButtonClass, operatorInputClass } from "@/components/shared";
import { CollapsibleText } from "@/components/ui";
import type { Environment } from "@/utils/api/types";
import { resolveCreatorLabel } from "@/utils/creator";

interface EnvironmentHeaderProps {
  env: Environment;
  editing: boolean;
  form: {
    category: string;
    tags: string[];
    description: string;
  };
  setForm: React.Dispatch<
    React.SetStateAction<{
      category: string;
      tags: string[];
      description: string;
    }>
  >;
  addTag: (tag: string) => void;
  removeTag: (tag: string) => void;
}

export function EnvironmentHeader({
  env,
  editing,
  form,
  setForm,
  addTag,
  removeTag,
}: EnvironmentHeaderProps) {
  const tags = editing ? form.tags : env.tags || [];
  const categoryValue = editing ? form.category : env.category || "";

  return (
    <>
      <div className="border-b border-gray-200 p-4">
        <div className="space-y-3">
          <div>
            <h1 className="text-lg font-semibold text-gray-950">{env.name}</h1>
            <p className="mt-0.5 text-xs text-gray-500">环境详情</p>
          </div>

          {!editing ? (
            <>
              {tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-md border border-gray-200 bg-gray-50 px-2 py-1 text-xs text-gray-600"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              {env.description ? (
                <CollapsibleText text={env.description} collapsedLines={3} />
              ) : (
                <p className="text-sm text-gray-400">暂无描述</p>
              )}
            </>
          ) : null}
        </div>

        {editing ? (
          <div className="mt-6 space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-700">
                  类别
                </label>
                <input
                  value={form.category}
                  onChange={(e) =>
                    setForm((prev) => ({ ...prev, category: e.target.value }))
                  }
                  placeholder="例如 indoor / outdoor / custom"
                  className={operatorInputClass("w-full")}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-700">
                  标签
                </label>
                <div className="mb-2 flex flex-wrap gap-2">
                  {form.tags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center gap-1 rounded-md border border-gray-200 bg-gray-50 px-2 py-1 text-xs text-gray-600"
                    >
                      {tag}
                      <button
                        type="button"
                        onClick={() => removeTag(tag)}
                        className="text-gray-500 hover:text-gray-700"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="输入标签"
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        const input = e.target as HTMLInputElement;
                        addTag(input.value);
                        input.value = "";
                      }
                    }}
                    className={operatorInputClass("min-w-0 flex-1")}
                  />
                  <button
                    type="button"
                    onClick={(e) => {
                      const input = e.currentTarget
                        .previousElementSibling as HTMLInputElement;
                      addTag(input.value);
                      input.value = "";
                    }}
                    className={operatorButtonClass("secondary")}
                  >
                    添加
                  </button>
                </div>
              </div>
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-gray-700">
                描述
              </label>
              <textarea
                value={form.description}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, description: e.target.value }))
                }
                rows={4}
                placeholder="填写环境描述或使用场景"
                className={operatorInputClass(
                  "h-auto min-h-24 w-full py-2 text-sm",
                )}
              />
            </div>
          </div>
        ) : null}
      </div>

      <div className="bg-gray-50/70 p-4">
        <div className="grid grid-cols-1 gap-3 text-xs text-gray-600 sm:grid-cols-2">
          <div>
            <span className="font-medium">类别：</span>
            {categoryValue || "未指定"}
          </div>
          <div>
            <span className="font-medium">创建者：</span>
            {resolveCreatorLabel(env.creator)}
          </div>
          <div>
            <span className="font-medium">创建时间：</span>
            {new Date(env.created_at).toLocaleString()}
          </div>
          {env.updated_at && (
            <div>
              <span className="font-medium">更新时间：</span>
              {new Date(env.updated_at).toLocaleString()}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
