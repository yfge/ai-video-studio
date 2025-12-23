"use client";

import Image from "next/image";
import { CollapsibleText } from "@/components/ui";
import type { VirtualIP } from "@/utils/api";
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
    <div className="p-6 sm:p-8 border-b border-gray-100">
      <div className="flex items-start space-x-6">
        <div className="w-24 h-24 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
          {virtualIP.default_avatar_url ? (
            <Image
              src={virtualIP.default_avatar_url}
              alt={virtualIP.name}
              width={96}
              height={96}
              className="w-24 h-24 rounded-full object-cover"
              unoptimized
            />
          ) : (
            <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                <label className="block text-sm font-medium text-gray-700 mb-1">名称 *</label>
                <input
                  type="text"
                  required
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
                <textarea
                  value={editForm.description}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={3}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">标签</label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {editForm.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded-full flex items-center"
                    >
                      {tag}
                      <button
                        type="button"
                        onClick={() => removeTag(tag)}
                        className="ml-1 text-blue-600 hover:text-blue-800"
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
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button
                    type="button"
                    onClick={(e) => {
                      const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                      addTag(input.value.trim());
                      input.value = "";
                    }}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
                  >
                    添加
                  </button>
                </div>
              </div>
            </form>
          ) : (
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">{virtualIP.name}</h2>
              {virtualIP.description ? (
                <div className="mb-4">
                  <CollapsibleText text={virtualIP.description} collapsedLines={2} />
                </div>
              ) : (
                <p className="text-sm text-gray-400 mb-4">暂无描述</p>
              )}
              {virtualIP.tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {virtualIP.tags.map((tag) => (
                    <span key={tag} className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
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
