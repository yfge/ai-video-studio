"use client";

import { operatorButtonClass } from "@/components/shared";
import type { UploadFormState } from "@/hooks/useVirtualIPImages";

interface ImageUploadFormProps {
  uploadForm: UploadFormState;
  setUploadForm: React.Dispatch<React.SetStateAction<UploadFormState>>;
  uploading: boolean;
  onUpload: () => void;
}

export function ImageUploadForm({
  uploadForm,
  setUploadForm,
  uploading,
  onUpload,
}: ImageUploadFormProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-950">上传图片</h3>
      <div className="grid grid-cols-1 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            选择文件
          </label>
          <input
            type="file"
            accept="image/*"
            onChange={(e) =>
              setUploadForm((prev) => ({
                ...prev,
                file: e.target.files?.[0] || null,
              }))
            }
            className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            图片类别
          </label>
          <select
            value={uploadForm.category}
            onChange={(e) =>
              setUploadForm((prev) => ({
                ...prev,
                category: e.target.value,
              }))
            }
            className="h-8 w-full rounded-md border border-gray-200 bg-white px-2 text-xs focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
          >
            <option value="portrait">肖像</option>
            <option value="full_body">全身</option>
            <option value="scene">场景</option>
            <option value="action">动作</option>
            <option value="emotion">情绪</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            标签（可选，逗号分隔）
          </label>
          <input
            type="text"
            value={uploadForm.tags}
            onChange={(e) =>
              setUploadForm((prev) => ({ ...prev, tags: e.target.value }))
            }
            placeholder="例如：微笑、晴天、户外"
            className="h-8 w-full rounded-md border border-gray-200 px-3 text-xs focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
          />
        </div>
        <div className="flex items-center">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={uploadForm.is_default}
              onChange={(e) =>
                setUploadForm((prev) => ({
                  ...prev,
                  is_default: e.target.checked,
                }))
              }
              className="mr-2"
            />
            <span className="text-sm text-gray-700">设为默认图片</span>
          </label>
        </div>
      </div>
      <div className="mt-4">
        <button
          onClick={onUpload}
          disabled={uploading || !uploadForm.file}
          className={operatorButtonClass("primary")}
        >
          {uploading ? "上传中..." : "上传图片"}
        </button>
      </div>
    </div>
  );
}
