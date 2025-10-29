'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { virtualIPAPI, VirtualIP } from '@/utils/api'

export default function VirtualIPDetail() {
  const params = useParams()
  const router = useRouter()
  const [virtualIP, setVirtualIP] = useState<VirtualIP | null>(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState({
    name: '',
    description: '',
    tags: [] as string[],
    background_story: ''
  })

  const ipId = Number(params.id)

  // 获取虚拟IP详情
  const fetchVirtualIP = async () => {
    try {
      setLoading(true)
      const response = await virtualIPAPI.getVirtualIP(ipId)
      
      if (response.success && response.data) {
        setVirtualIP(response.data)
        setEditForm({
          name: response.data.name,
          description: response.data.description || '',
          tags: response.data.tags || [],
          background_story: response.data.background_story || ''
        })
      } else {
        console.error('获取虚拟IP详情失败:', response.error)
        showAlert({ message: '获取虚拟IP详情失败', variant: 'error' })
      }
    } catch (error) {
      console.error('获取虚拟IP详情出错:', error)
      showAlert({ message: '获取虚拟IP详情失败', variant: 'error' })
    } finally {
      setLoading(false)
    }
  }

  // 更新虚拟IP
  const handleUpdateIP = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const response = await virtualIPAPI.updateVirtualIP(ipId, editForm)
      if (response.success && response.data) {
        setVirtualIP(response.data)
        setEditing(false)
        showAlert({ message: '更新成功', variant: 'success' })
      } else {
        showAlert({ message: `更新失败: ${response.error || '未知错误'}`, variant: 'error' })
      }
    } catch (error) {
      console.error('更新虚拟IP出错:', error)
      showAlert({ message: '更新失败，请重试', variant: 'error' })
    }
  }

  // 删除虚拟IP
  const handleDeleteIP = async () => {
    if (!confirm('确定要删除这个虚拟IP吗？此操作不可恢复！')) return
    
    try {
      const response = await virtualIPAPI.deleteVirtualIP(ipId)
      if (response.success) {
        showAlert({ message: '删除成功', variant: 'success' })
        router.push('/virtual-ip')
      } else {
        showAlert({ message: `删除失败: ${response.error || '未知错误'}`, variant: 'error' })
      }
    } catch (error) {
      console.error('删除虚拟IP出错:', error)
      showAlert({ message: '删除失败，请重试', variant: 'error' })
    }
  }

  // 标签管理
  const addTag = (tag: string) => {
    if (tag && !editForm.tags.includes(tag)) {
      setEditForm({ ...editForm, tags: [...editForm.tags, tag] })
    }
  }

  const removeTag = (tagToRemove: string) => {
    setEditForm({ ...editForm, tags: editForm.tags.filter(tag => tag !== tagToRemove) })
  }

  useEffect(() => {
    if (ipId) {
      fetchVirtualIP()
    }
  }, [ipId])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex justify-center items-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!virtualIP) {
    return (
      <div className="min-h-screen bg-gray-50 flex justify-center items-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">虚拟IP不存在</h2>
          <Link href="/virtual-ip" className="text-blue-600 hover:text-blue-800">
            返回虚拟IP列表
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-8">
              <Link href="/virtual-ip" className="text-gray-500 hover:text-gray-900">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </Link>
              <h1 className="text-2xl font-bold text-gray-900">虚拟IP详情</h1>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                href={`/virtual-ip/${ipId}/images`}
                className="text-green-600 hover:text-green-800 px-4 py-2 rounded-md border border-green-600 hover:bg-green-50"
              >
                管理图像
              </Link>
              <button
                onClick={() => setEditing(!editing)}
                className="text-blue-600 hover:text-blue-800 px-4 py-2 rounded-md border border-blue-600 hover:bg-blue-50"
              >
                {editing ? '取消编辑' : '编辑'}
              </button>
              <button
                onClick={handleDeleteIP}
                className="text-red-600 hover:text-red-800 px-4 py-2 rounded-md border border-red-600 hover:bg-red-50"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white shadow rounded-lg overflow-hidden">
          {/* 头像和基本信息 */}
          <div className="p-8 border-b">
            <div className="flex items-start space-x-6">
              <div className="w-24 h-24 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
                {virtualIP.default_avatar_url ? (
                  <img src={virtualIP.default_avatar_url} alt={virtualIP.name} className="w-24 h-24 rounded-full object-cover" />
                ) : (
                  <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                )}
              </div>
              
              <div className="flex-1">
                {editing ? (
                  <form onSubmit={handleUpdateIP} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        名称 *
                      </label>
                      <input
                        type="text"
                        required
                        value={editForm.name}
                        onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        描述
                      </label>
                      <textarea
                        value={editForm.description}
                        onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        rows={3}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        标签
                      </label>
                      <div className="flex flex-wrap gap-2 mb-2">
                        {editForm.tags.map((tag) => (
                          <span
                            key={tag}
                            className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded-full flex items-center"
                          >
                            {tag}
                            <button
                              type="button"
                              onClick={() => removeTag(tag)}
                              className="ml-1 text-blue-600 hover:text-blue-800"
                            >
                              ×
                            </button>
                          </span>
                        ))}
                      </div>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          placeholder="输入标签"
                          onKeyPress={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault()
                              const input = e.target as HTMLInputElement
                              addTag(input.value.trim())
                              input.value = ''
                            }
                          }}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                        <button
                          type="button"
                          onClick={(e) => {
                            const input = e.currentTarget.previousElementSibling as HTMLInputElement
                            addTag(input.value.trim())
                            input.value = ''
                          }}
                          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
                        >
                          添加
                        </button>
                      </div>
                    </div>

                    <div className="flex justify-end space-x-3">
                      <button
                        type="button"
                        onClick={() => setEditing(false)}
                        className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                      >
                        取消
                      </button>
                      <button
                        type="submit"
                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                      >
                        保存
                      </button>
                    </div>
                  </form>
                ) : (
                  <div>
                    <h2 className="text-3xl font-bold text-gray-900 mb-2">{virtualIP.name}</h2>
                    {virtualIP.description && (
                      <p className="text-gray-600 mb-4">{virtualIP.description}</p>
                    )}
                    {virtualIP.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {virtualIP.tags.map((tag) => (
                          <span
                            key={tag}
                            className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* 背景故事 */}
          {virtualIP.background_story && (
            <div className="p-8 border-b">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">背景故事</h3>
              {editing ? (
                <textarea
                  value={editForm.background_story}
                  onChange={(e) => setEditForm({ ...editForm, background_story: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={6}
                />
              ) : (
                <div className="prose max-w-none">
                  <p className="text-gray-700 whitespace-pre-wrap">{virtualIP.background_story}</p>
                </div>
              )}
            </div>
          )}

          {/* 创建信息 */}
          <div className="p-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-500">
              <div>
                <span className="font-medium">创建时间：</span>
                {new Date(virtualIP.created_at).toLocaleString()}
              </div>
              {virtualIP.updated_at && (
                <div>
                  <span className="font-medium">更新时间：</span>
                  {new Date(virtualIP.updated_at).toLocaleString()}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
} 
