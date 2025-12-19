"use client";

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
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h3 className="text-lg font-semibold mb-4">上传图片</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {uploading ? "上传中..." : "上传图片"}
        </button>
      </div>
    </div>
  );
}
