"use client";

import type { VirtualIP } from "@/utils/api";

interface ImagePageHeaderProps {
  virtualIP: VirtualIP;
  onBack: () => void;
  onShowGenerateForm: () => void;
  onShowUploadForm: () => void;
  onViewTasks: () => void;
}

export function ImagePageHeader({
  virtualIP,
  onBack,
  onShowGenerateForm,
  onShowUploadForm,
  onViewTasks,
}: ImagePageHeaderProps) {
  return (
    <>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {virtualIP.name} - Image Management
            </h1>
            <p className="mt-2 text-gray-600">{virtualIP.description}</p>
          </div>
          <button
            onClick={onBack}
            className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
          >
            Back to Details
          </button>
        </div>
      </div>

      {/* Action buttons */}
      <div className="mb-6 flex gap-4">
        <button
          onClick={onShowGenerateForm}
          className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2"
        >
          <span>AI Generate Image</span>
        </button>
        <button
          onClick={onShowUploadForm}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <span>Upload Image</span>
        </button>
        <button
          onClick={onViewTasks}
          className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 flex items-center gap-2"
        >
          <span>View Tasks</span>
        </button>
      </div>
    </>
  );
}
