"use client";

import { operatorButtonClass } from "@/components/shared";

interface StatusSettingsProps {
  isActive: boolean;
  isPublic: boolean;
  onActiveChange: (value: boolean) => void;
  onPublicChange: (value: boolean) => void;
}

export function VirtualIPStatusSettings({
  isActive,
  isPublic,
  onActiveChange,
  onPublicChange,
}: StatusSettingsProps) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-gray-700">
        状态设置
      </label>
      <div className="flex flex-col gap-3 rounded-md border border-gray-200 bg-gray-50 p-3 sm:flex-row">
        <label className="inline-flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={isActive}
            onChange={(event) => onActiveChange(event.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          启用角色
        </label>
        <label className="inline-flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={isPublic}
            onChange={(event) => onPublicChange(event.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          公开展示
        </label>
      </div>
    </div>
  );
}

export function VirtualIPCreateFooter({ onClose }: { onClose: () => void }) {
  return (
    <div className="flex justify-end gap-3 border-t pt-4">
      <button
        type="button"
        onClick={onClose}
        className={operatorButtonClass("secondary")}
      >
        取消
      </button>
      <button type="submit" className={operatorButtonClass("primary")}>
        创建 IP
      </button>
    </div>
  );
}
