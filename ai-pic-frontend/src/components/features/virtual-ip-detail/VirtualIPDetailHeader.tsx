"use client";

import Link from "next/link";

interface VirtualIPDetailHeaderProps {
  ipKey: string;
  businessId?: string;
  editing: boolean;
  setEditing: (editing: boolean) => void;
  onDelete: () => void;
}

export function VirtualIPDetailHeader({
  ipKey,
  businessId,
  editing,
  setEditing,
  onDelete,
}: VirtualIPDetailHeaderProps) {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-6">
          <div className="flex items-center space-x-8">
            <Link href="/virtual-ip" className="text-gray-500 hover:text-gray-900">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </Link>
            <h1 className="text-2xl font-bold text-gray-900">虚拟IP详情</h1>
          </div>
          <div className="flex items-center space-x-4">
            <Link
              href={`/virtual-ip/${businessId || ipKey}/images`}
              className="text-green-600 hover:text-green-800 px-4 py-2 rounded-md border border-green-600 hover:bg-green-50"
            >
              管理图片
            </Link>
            <button
              onClick={() => setEditing(!editing)}
              className="text-blue-600 hover:text-blue-800 px-4 py-2 rounded-md border border-blue-600 hover:bg-blue-50"
            >
              {editing ? "取消编辑" : "编辑"}
            </button>
            <button
              onClick={onDelete}
              className="text-red-600 hover:text-red-800 px-4 py-2 rounded-md border border-red-600 hover:bg-red-50"
            >
              删除
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
