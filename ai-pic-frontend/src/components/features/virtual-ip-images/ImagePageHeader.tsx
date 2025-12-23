"use client";

import type { VirtualIP } from "@/utils/api";

interface ImagePageHeaderProps {
  virtualIP: VirtualIP;
  showVirtualIPInfo?: boolean;
  onBack?: () => void;
  backLabel?: string;
  onShowGenerateForm: () => void;
  onShowUploadForm: () => void;
  onViewTasks: () => void;
}

export function ImagePageHeader({
  virtualIP,
  showVirtualIPInfo = true,
  onBack,
  backLabel,
  onShowGenerateForm,
  onShowUploadForm,
  onViewTasks,
}: ImagePageHeaderProps) {
  return (
    <>
      {/* Header */}
      <div className="mb-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-gray-900">
              {showVirtualIPInfo ? `${virtualIP.name} - 图片管理` : "图片管理"}
            </h2>
            {showVirtualIPInfo && virtualIP.description ? (
              <p className="mt-1 text-sm text-gray-600">{virtualIP.description}</p>
            ) : null}
          </div>
          {onBack ? (
            <button
              onClick={onBack}
              className="inline-flex items-center justify-center rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              {backLabel || "返回详情"}
            </button>
          ) : null}
        </div>
      </div>

      {/* Action buttons */}
      <div className="mb-6 flex flex-wrap gap-3">
        <button
          onClick={onShowGenerateForm}
          className="bg-green-600 text-white px-5 py-2 rounded-md hover:bg-green-700 flex items-center gap-2"
        >
          <span>AI 生成图片</span>
        </button>
        <button
          onClick={onShowUploadForm}
          className="bg-blue-600 text-white px-5 py-2 rounded-md hover:bg-blue-700 flex items-center gap-2"
        >
          <span>上传图片</span>
        </button>
        <button
          onClick={onViewTasks}
          className="bg-purple-600 text-white px-5 py-2 rounded-md hover:bg-purple-700 flex items-center gap-2"
        >
          <span>查看任务</span>
        </button>
      </div>
    </>
  );
}
