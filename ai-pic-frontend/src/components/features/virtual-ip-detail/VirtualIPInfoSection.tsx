"use client";

import Image from "next/image";
import { CollapsibleText } from "@/components/ui";
import type { VirtualIP } from "@/utils/api/types";
import type { EditFormState } from "@/hooks/useVirtualIPDetail";

interface VirtualIPInfoSectionProps {
  virtualIP: VirtualIP;
  editing: boolean;
  editForm: EditFormState;
  setEditForm: React.Dispatch<React.SetStateAction<EditFormState>>;
  onSubmit: (e: React.FormEvent) => void;
  addTag: (tag: string) => void;
  removeTag: (tag: string) => void;
  formId?: string;
}

export function VirtualIPInfoSection({
  virtualIP,
  editing,
  editForm,
  setEditForm,
  onSubmit,
  addTag,
  removeTag,
  formId,
}: VirtualIPInfoSectionProps) {
  return (
    <div className="border-b border-gray-100 p-5">
      <div className="flex items-start gap-5">
        <div className="flex h-24 w-24 flex-shrink-0 items-center justify-center rounded-lg border border-gray-200 bg-gray-50">
          {virtualIP.default_avatar_url ? (
            <Image
              src={virtualIP.default_avatar_url}
              alt={virtualIP.name}
              width={96}
              height={96}
              className="h-24 w-24 rounded-lg object-cover"
              unoptimized
            />
          ) : (
            <svg
              className="w-12 h-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          )}
        </div>

        <div className="flex-1">
          {editing ? (
            <form id={formId} onSubmit={onSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  名称 *
                </label>
                <input
                  type="text"
                  required
                  value={editForm.name}
                  onChange={(e) =>
                    setEditForm({ ...editForm, name: e.target.value })
                  }
                  className="h-8 w-full rounded-md border border-gray-200 px-3 text-sm focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  描述
                </label>
                <textarea
                  value={editForm.description}
                  onChange={(e) =>
                    setEditForm({ ...editForm, description: e.target.value })
                  }
                  className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
                  rows={3}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  标签
                </label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {editForm.tags.map((tag) => (
                    <span
                      key={tag}
                      className="flex items-center rounded-md border border-blue-200 bg-blue-50 px-2 py-1 text-xs text-blue-700"
                    >
                      {tag}
                      <button
                        type="button"
                        onClick={() => removeTag(tag)}
                        className="ml-1 text-blue-500 hover:text-blue-700"
                      >
                        x
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="输入标签"
                    onKeyPress={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        const input = e.target as HTMLInputElement;
                        addTag(input.value.trim());
                        input.value = "";
                      }
                    }}
                    className="h-8 flex-1 rounded-md border border-gray-200 px-3 text-xs focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
                  />
                  <button
                    type="button"
                    onClick={(e) => {
                      const input = e.currentTarget
                        .previousElementSibling as HTMLInputElement;
                      addTag(input.value.trim());
                      input.value = "";
                    }}
                    className="h-8 rounded-md border border-gray-200 bg-white px-3 text-xs text-gray-700 hover:bg-gray-50"
                  >
                    添加
                  </button>
                </div>
              </div>
            </form>
          ) : (
            <div>
              <h2 className="mb-2 text-xl font-semibold text-gray-950">
                {virtualIP.name}
              </h2>
              {virtualIP.description ? (
                <div className="mb-4">
                  <CollapsibleText
                    text={virtualIP.description}
                    collapsedLines={2}
                  />
                </div>
              ) : (
                <p className="text-sm text-gray-400 mb-4">暂无描述</p>
              )}
              {virtualIP.tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {virtualIP.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-md border border-gray-200 bg-gray-50 px-2 py-1 text-xs text-gray-600"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
