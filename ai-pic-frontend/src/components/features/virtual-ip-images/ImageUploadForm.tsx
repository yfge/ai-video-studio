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
      <h3 className="text-lg font-semibold mb-4">Upload Image</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select File
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
            Image Category
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
            <option value="portrait">Portrait</option>
            <option value="full_body">Full Body</option>
            <option value="scene">Scene</option>
            <option value="action">Action</option>
            <option value="emotion">Emotion</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Tags (optional, comma-separated)
          </label>
          <input
            type="text"
            value={uploadForm.tags}
            onChange={(e) =>
              setUploadForm((prev) => ({ ...prev, tags: e.target.value }))
            }
            placeholder="e.g., smiling, sunny, outdoor"
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
            <span className="text-sm text-gray-700">Set as default image</span>
          </label>
        </div>
      </div>
      <div className="mt-4">
        <button
          onClick={onUpload}
          disabled={uploading || !uploadForm.file}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {uploading ? "Uploading..." : "Upload Image"}
        </button>
      </div>
    </div>
  );
}
