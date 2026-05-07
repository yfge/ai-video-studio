"use client";

import { CollapsibleText } from "@/components/ui";
import type { EditFormState } from "@/hooks/useVirtualIPDetail";
import type { VirtualIP } from "@/utils/api/types";

interface VirtualIPAdditionalInfoSectionProps {
  virtualIP: VirtualIP;
  editing: boolean;
  editForm: EditFormState;
  setEditForm: React.Dispatch<React.SetStateAction<EditFormState>>;
}

const parseReferenceImages = (value: string) =>
  value
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);

const formatReferenceImages = (items: string[]) => items.join("\n");

const statusBadge = (enabled: boolean, onLabel: string, offLabel: string) => (
  <span
    className={[
      "inline-flex items-center rounded-md border px-2 py-1 text-xs font-medium",
      enabled
        ? "border-green-200 bg-green-50 text-green-700"
        : "border-gray-200 bg-gray-50 text-gray-600",
    ].join(" ")}
  >
    {enabled ? onLabel : offLabel}
  </span>
);

export function VirtualIPAdditionalInfoSection({
  virtualIP,
  editing,
  editForm,
  setEditForm,
}: VirtualIPAdditionalInfoSectionProps) {
  const hasBiography = Boolean(virtualIP.biography?.trim());
  const hasStylePrompt = Boolean(virtualIP.style_prompt?.trim());
  const hasStyleReferences =
    (virtualIP.style_reference_images || []).length > 0;

  return (
    <div className="space-y-5 border-b border-gray-100 p-5">
      <div>
        <h3 className="text-sm font-semibold text-gray-950">补充信息</h3>
        <p className="text-sm text-gray-500">
          补充人物小传、风格提示词与公开状态。
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            人物小传
          </label>
          {editing ? (
            <textarea
              value={editForm.biography}
              onChange={(e) =>
                setEditForm({ ...editForm, biography: e.target.value })
              }
              rows={4}
              className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
              placeholder="补充角色的小传、经历或性格补充"
            />
          ) : hasBiography ? (
            <CollapsibleText
              text={virtualIP.biography || ""}
              collapsedLines={3}
            />
          ) : (
            <p className="text-sm text-gray-400">未填写</p>
          )}
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            风格提示词
          </label>
          {editing ? (
            <textarea
              value={editForm.style_prompt}
              onChange={(e) =>
                setEditForm({ ...editForm, style_prompt: e.target.value })
              }
              rows={4}
              className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
              placeholder="用于图像生成的风格描述"
            />
          ) : hasStylePrompt ? (
            <CollapsibleText
              text={virtualIP.style_prompt || ""}
              collapsedLines={3}
            />
          ) : (
            <p className="text-sm text-gray-400">未填写</p>
          )}
        </div>
      </div>

      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          风格参考图
        </label>
        {editing ? (
          <textarea
            value={formatReferenceImages(editForm.style_reference_images)}
            onChange={(e) =>
              setEditForm({
                ...editForm,
                style_reference_images: parseReferenceImages(e.target.value),
              })
            }
            rows={3}
            className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
            placeholder="每行一个参考图 URL"
          />
        ) : hasStyleReferences ? (
          <div className="space-y-2">
            {virtualIP.style_reference_images?.map((url) => (
              <a
                key={url}
                href={url}
                target="_blank"
                rel="noreferrer"
                className="block text-sm text-blue-600 hover:underline line-clamp-1"
              >
                {url}
              </a>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400">未设置</p>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="flex items-center justify-between rounded-md border border-gray-200 px-4 py-3">
          <div>
            <p className="text-sm font-medium text-gray-700">可用状态</p>
            <p className="text-xs text-gray-500">停用后不可用于生成</p>
          </div>
          {editing ? (
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={editForm.is_active}
                onChange={(e) =>
                  setEditForm({ ...editForm, is_active: e.target.checked })
                }
                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              {editForm.is_active ? "启用" : "停用"}
            </label>
          ) : (
            statusBadge(virtualIP.is_active, "启用", "停用")
          )}
        </div>

        <div className="flex items-center justify-between rounded-md border border-gray-200 px-4 py-3">
          <div>
            <p className="text-sm font-medium text-gray-700">公开状态</p>
            <p className="text-xs text-gray-500">公开后可被他人查看</p>
          </div>
          {editing ? (
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={editForm.is_public}
                onChange={(e) =>
                  setEditForm({ ...editForm, is_public: e.target.checked })
                }
                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              {editForm.is_public ? "公开" : "私有"}
            </label>
          ) : (
            statusBadge(virtualIP.is_public, "公开", "私有")
          )}
        </div>
      </div>
    </div>
  );
}
