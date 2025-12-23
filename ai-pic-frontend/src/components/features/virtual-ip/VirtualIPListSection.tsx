'use client'

import Image from 'next/image'
import Link from 'next/link'
import type { VirtualIP } from '@/utils/api'
import { resolveCreatorLabel } from '@/utils/creator'

interface VirtualIPListSectionProps {
  loading: boolean
  virtualIPs: VirtualIP[]
  searchTerm: string
  onSearchTermChange: (value: string) => void
  allTags: string[]
  selectedTags: string[]
  onToggleTag: (tag: string) => void
  onOpenCreate: () => void
  onDelete: (bizId: string) => void
}

export function VirtualIPListSection({
  loading,
  virtualIPs,
  searchTerm,
  onSearchTermChange,
  allTags,
  selectedTags,
  onToggleTag,
  onOpenCreate,
  onDelete,
}: VirtualIPListSectionProps) {
  return (
    <div className="space-y-8">
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="flex-1 max-w-md">
            <input
              type="text"
              placeholder="搜索虚拟IP..."
              value={searchTerm}
              onChange={(e) => onSearchTermChange(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            {allTags.map((tag) => (
              <button
                key={tag}
                onClick={() => onToggleTag(tag)}
                className={`px-3 py-1 rounded-full text-sm font-medium ${
                  selectedTags.includes(tag)
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {tag}
              </button>
            ))}
          </div>

          <button
            onClick={onOpenCreate}
            className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-3 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 flex items-center gap-3 shadow-lg"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            <span className="font-medium">创建虚拟IP</span>
            <div className="flex items-center gap-1 text-xs bg-white bg-opacity-20 px-2 py-1 rounded-full">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
              AI助手
            </div>
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : virtualIPs.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-4">
            <svg className="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">暂无虚拟IP</h3>
          <p className="text-gray-500 mb-4">开始创建你的第一个虚拟IP吧！</p>
          <button
            onClick={onOpenCreate}
            className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            创建虚拟IP
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {virtualIPs.map((ip) => (
            <div
              key={ip.business_id}
              className="bg-white shadow rounded-lg overflow-hidden hover:shadow-lg transition-shadow"
            >
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
                      {ip.default_avatar_url ? (
                        <Image
                          src={ip.default_avatar_url}
                          alt={ip.name}
                          width={48}
                          height={48}
                          className="w-12 h-12 rounded-full object-cover"
                          unoptimized
                        />
                      ) : (
                        <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                      )}
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{ip.name}</h3>
                      <p className="text-sm text-gray-500">创建者：{resolveCreatorLabel(ip.creator)}</p>
                      <p className="text-sm text-gray-500">创建于 {new Date(ip.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <Link href={`/virtual-ip/${ip.business_id}`} className="text-blue-600 hover:text-blue-800">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    </Link>
                    <button onClick={() => onDelete(ip.business_id)} className="text-red-600 hover:text-red-800">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>

                {ip.description && <p className="text-gray-600 mb-4 line-clamp-2">{ip.description}</p>}

                {ip.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {ip.tags.map((tag) => (
                      <span key={tag} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}

                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">{ip.background_story ? '有背景故事' : '无背景故事'}</span>
                  <Link href={`/virtual-ip/${ip.business_id}`} className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                    查看详情 →
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
