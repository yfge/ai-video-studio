"use client";

import type { VirtualIP } from "@/utils/api/types";
import {
  OperatorState,
  StatusPill,
  operatorButtonClass,
} from "@/components/shared";

interface CharacterSelectorProps {
  virtualIPs: VirtualIP[];
  selectedIds: number[];
  onToggle: (id: number) => void;
  onNavigateToVirtualIP: () => void;
}

export function CharacterSelector({
  virtualIPs,
  selectedIds,
  onToggle,
  onNavigateToVirtualIP,
}: CharacterSelectorProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        选择角色 * (至少选择一个)
        <span className="text-blue-600 ml-2">
          已选择: {selectedIds.length} 个
        </span>
      </label>

      {virtualIPs.length === 0 ? (
        <OperatorState
          title="暂无可用角色"
          detail="请先创建虚拟 IP 角色，然后再生成故事。"
          action={
            <button
              type="button"
              onClick={onNavigateToVirtualIP}
              className={operatorButtonClass("primary")}
            >
              创建虚拟 IP
            </button>
          }
        />
      ) : (
        <div className="rounded-md border border-gray-200 bg-gray-50 p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 max-h-64 overflow-y-auto">
            {virtualIPs.map((ip) => (
              <label
                key={ip.id}
                className={`flex items-center p-3 border-2 rounded-lg cursor-pointer transition-all ${
                  selectedIds.includes(ip.id)
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-200 bg-white hover:bg-gray-50 hover:border-gray-300"
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedIds.includes(ip.id)}
                  onChange={() => onToggle(ip.id)}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2 mr-3"
                />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900 truncate">
                    {ip.name}
                  </div>
                  <div className="text-sm text-gray-500 line-clamp-2">
                    {ip.description}
                  </div>
                  {ip.tags && ip.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {ip.tags.slice(0, 2).map((tag, index) => (
                        <StatusPill key={index} tone="gray">
                          {tag}
                        </StatusPill>
                      ))}
                    </div>
                  )}
                </div>
              </label>
            ))}
          </div>

          {selectedIds.length > 0 && (
            <div className="mt-3 rounded-md border border-blue-200 bg-blue-50 p-2">
              <p className="text-sm text-blue-800">
                已选择角色:{" "}
                {selectedIds
                  .map((id) => {
                    const ip = virtualIPs.find((v) => v.id === id);
                    return ip?.name;
                  })
                  .filter(Boolean)
                  .join(", ")}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
