"use client"

import Link from "next/link"

interface EnvironmentDetailHeaderProps {
  editing: boolean
  saving: boolean
  onEdit: () => void
  onCancel: () => void
  onSave: () => void
}

export function EnvironmentDetailHeader({
  editing,
  saving,
  onEdit,
  onCancel,
  onSave,
}: EnvironmentDetailHeaderProps) {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-4 py-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center space-x-6">
            <Link href="/environments" className="text-gray-500 hover:text-gray-900">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </Link>
            <h1 className="text-2xl font-bold text-gray-900">环境详情</h1>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            {editing ? (
              <>
                <button
                  onClick={onSave}
                  disabled={saving}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-60"
                >
                  {saving ? "保存中..." : "保存"}
                </button>
                <button
                  onClick={onCancel}
                  disabled={saving}
                  className="text-blue-600 hover:text-blue-800 px-4 py-2 rounded-md border border-blue-600 hover:bg-blue-50 disabled:opacity-60"
                >
                  取消
                </button>
              </>
            ) : (
              <button
                onClick={onEdit}
                className="text-blue-600 hover:text-blue-800 px-4 py-2 rounded-md border border-blue-600 hover:bg-blue-50"
              >
                编辑
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
