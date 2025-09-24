'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { virtualIPAPI, VirtualIP } from '@/utils/api'
import AuthGuard from '@/components/AuthGuard'
import Navigation from '@/components/Navigation'
import SmartInputField from '@/components/SmartInputField'

function VirtualIPListContent() {
  const [virtualIPs, setVirtualIPs] = useState<VirtualIP[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newIP, setNewIP] = useState({
    name: '',
    description: '',
    tags: [] as string[],
    background_story: '',
    biography: ''
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
        resetForm()
      } else {
        alert('创建失败: ' + (response.error || '未知错误'))
      }
    } catch (error) {
      console.error('创建虚拟IP出错:', error)
      alert('创建失败，请重试')
    }
  }

  // 重置表单
  const resetForm = () => {
    setNewIP({ name: '', description: '', tags: [], background_story: '', biography: '' })
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
      <Navigation title="虚拟IP管理" />

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
              className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-3 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 flex items-center gap-3 shadow-lg"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              <span className="font-medium">创建虚拟IP</span>
              <div className="flex items-center gap-1 text-xs bg-white bg-opacity-20 px-2 py-1 rounded-full">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                AI助手
              </div>
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
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center gap-3 mb-6">
              <div className="h-10 w-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center">
                <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  创建虚拟IP
                </h2>
                <p className="text-sm text-gray-500">
                  AI智能助手将协助您完成每个字段的填写
                </p>
              </div>
            </div>
            
            <form onSubmit={handleCreateIP}>
              <div className="space-y-6">
                <SmartInputField
                  label="名称 *"
                  value={newIP.name}
                  onChange={(value) => setNewIP({ ...newIP, name: value })}
                  placeholder="输入虚拟IP名称，如：小雅、李教授、小明等"
                  type="input"
                  showAIAssist={false}
                />

                <SmartInputField
                  label="角色描述"
                  value={newIP.description}
                  onChange={(value) => setNewIP({ ...newIP, description: value })}
                  placeholder="描述这个角色的基本特征、性格、外貌等"
                  type="textarea"
                  rows={3}
                  aiSuggestType="description"
                  contextData={{ name: newIP.name }}
                />

                <SmartInputField
                  label="背景故事"
                  value={newIP.background_story}
                  onChange={(value) => setNewIP({ ...newIP, background_story: value })}
                  placeholder="描述角色的成长经历、重要事件、生活背景等"
                  type="textarea"
                  rows={4}
                  aiSuggestType="background_story"
                  contextData={{ name: newIP.name, description: newIP.description }}
                />

                <SmartInputField
                  label="人物小传"
                  value={newIP.biography}
                  onChange={(value) => setNewIP({ ...newIP, biography: value })}
                  placeholder="详细介绍角色的生平、成就、重要关系等"
                  type="textarea"
                  rows={4}
                  aiSuggestType="biography"
                  contextData={{ name: newIP.name, description: newIP.description, basicInfo: newIP.background_story }}
                />

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

              </div>

              <div className="flex justify-end space-x-3 mt-8 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateForm(false)
                    resetForm()
                  }}
                  className="px-6 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-md hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg"
                >
                  创建虚拟IP
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  )
}

export default function VirtualIPList() {
  return (
    <AuthGuard>
      <VirtualIPListContent />
    </AuthGuard>
  )
} 