'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { virtualIPAPI, VirtualIP } from '@/utils/api'

export default function VirtualIPList() {
  const [virtualIPs, setVirtualIPs] = useState<VirtualIP[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newIP, setNewIP] = useState({
    name: '',
    description: '',
    tags: [] as string[],
    background_story: ''
  })

  // 获取虚拟IP列表
  const fetchVirtualIPs = async () => {
    try {
      setLoading(true)
      const response = await virtualIPAPI.getVirtualIPs({
        search: searchTerm || undefined,
        tags: selectedTags.length > 0 ? selectedTags : undefined
      })
      
      if (response.success && response.data) {
        setVirtualIPs(response.data)
      } else {
        console.error('获取虚拟IP列表失败:', response.error)
      }
    } catch (error) {
      console.error('获取虚拟IP列表出错:', error)
    } finally {
      setLoading(false)
    }
  }

  // 创建虚拟IP
  const handleCreateIP = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const response = await virtualIPAPI.createVirtualIP(newIP)
      if (response.success && response.data) {
        setVirtualIPs([response.data, ...virtualIPs])
        setShowCreateForm(false)
        setNewIP({ name: '', description: '', tags: [], background_story: '' })
      } else {
        alert('创建失败: ' + (response.error || '未知错误'))
      }
    } catch (error) {
      console.error('创建虚拟IP出错:', error)
      alert('创建失败，请重试')
    }
  }

  // 删除虚拟IP
  const handleDeleteIP = async (id: number) => {
    if (!confirm('确定要删除这个虚拟IP吗？')) return
    
    try {
      const response = await virtualIPAPI.deleteVirtualIP(id)
      if (response.success) {
        setVirtualIPs(virtualIPs.filter(ip => ip.id !== id))
      } else {
        alert('删除失败: ' + (response.error || '未知错误'))
      }
    } catch (error) {
      console.error('删除虚拟IP出错:', error)
      alert('删除失败，请重试')
    }
  }

  // 标签管理
  const addTag = (tag: string) => {
    if (tag && !newIP.tags.includes(tag)) {
      setNewIP({ ...newIP, tags: [...newIP.tags, tag] })
    }
  }

  const removeTag = (tagToRemove: string) => {
    setNewIP({ ...newIP, tags: newIP.tags.filter(tag => tag !== tagToRemove) })
  }

  // 搜索和筛选
  useEffect(() => {
    fetchVirtualIPs()
  }, [searchTerm, selectedTags])

  // 获取所有标签用于筛选
  const allTags = Array.from(new Set(virtualIPs.flatMap(ip => ip.tags)))

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-8">
              <h1 className="text-2xl font-bold text-gray-900">虚拟IP管理</h1>
              <nav className="flex space-x-8">
                <Link href="/virtual-ip" className="text-blue-600 border-b-2 border-blue-600 px-3 py-2 text-sm font-medium">
                  虚拟IP
                </Link>
                <Link href="/tasks" className="text-gray-500 hover:text-gray-900 px-3 py-2 text-sm font-medium">
                  任务管理
                </Link>
                <Link href="/gallery" className="text-gray-500 hover:text-gray-900 px-3 py-2 text-sm font-medium">
                  图片画廊
                </Link>
              </nav>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">欢迎，用户</span>
              <button className="text-gray-500 hover:text-gray-900">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 搜索和筛选区域 */}
        <div className="bg-white shadow rounded-lg p-6 mb-8">
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            <div className="flex-1 max-w-md">
              <input
                type="text"
                placeholder="搜索虚拟IP..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            <div className="flex flex-wrap gap-2">
              {allTags.map(tag => (
                <button
                  key={tag}
                  onClick={() => setSelectedTags(prev => 
                    prev.includes(tag) 
                      ? prev.filter(t => t !== tag)
                      : [...prev, tag]
                  )}
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
              onClick={() => setShowCreateForm(true)}
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors"
            >
              新建虚拟IP
            </button>
          </div>
        </div>

        {/* 虚拟IP列表 */}
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
              onClick={() => setShowCreateForm(true)}
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors"
            >
              创建虚拟IP
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {virtualIPs.map((ip) => (
              <div key={ip.id} className="bg-white shadow rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
                        {ip.default_avatar_url ? (
                          <img src={ip.default_avatar_url} alt={ip.name} className="w-12 h-12 rounded-full object-cover" />
                        ) : (
                          <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                        )}
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">{ip.name}</h3>
                        <p className="text-sm text-gray-500">创建于 {new Date(ip.created_at).toLocaleDateString()}</p>
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <Link
                        href={`/virtual-ip/${ip.id}`}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                      </Link>
                      <button
                        onClick={() => handleDeleteIP(ip.id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                  
                  {ip.description && (
                    <p className="text-gray-600 mb-4 line-clamp-2">{ip.description}</p>
                  )}
                  
                  {ip.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-4">
                      {ip.tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">
                      {ip.background_story ? '有背景故事' : '无背景故事'}
                    </span>
                    <Link
                      href={`/virtual-ip/${ip.id}`}
                      className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                    >
                      查看详情 →
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* 创建虚拟IP弹窗 */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">创建虚拟IP</h2>
            
            <form onSubmit={handleCreateIP}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    名称 *
                  </label>
                  <input
                    type="text"
                    required
                    value={newIP.name}
                    onChange={(e) => setNewIP({ ...newIP, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="输入虚拟IP名称"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    描述
                  </label>
                  <textarea
                    value={newIP.description}
                    onChange={(e) => setNewIP({ ...newIP, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows={3}
                    placeholder="输入虚拟IP描述"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    标签
                  </label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {newIP.tags.map((tag) => (
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

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    背景故事
                  </label>
                  <textarea
                    value={newIP.background_story}
                    onChange={(e) => setNewIP({ ...newIP, background_story: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows={4}
                    placeholder="输入虚拟IP的背景故事"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  创建
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
} 