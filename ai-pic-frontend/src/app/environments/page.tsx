'use client'

import { useCallback, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import AuthGuard from '@/components/AuthGuard'
import Navigation from '@/components/Navigation'
import { storyStructureAPI, type Environment, type EnvironmentCreate } from '@/utils/api'
import { useAlertModal } from '@/components/AlertModalProvider'
import { CreationOverlay } from '@/components/CreationOverlay'

function EnvironmentsPageContent() {
  const router = useRouter()
  const { showAlert } = useAlertModal()
  const [list, setList] = useState<Environment[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [creating, setCreating] = useState(false)
  const [newEnv, setNewEnv] = useState<EnvironmentCreate>({
    name: '',
    category: 'indoor',
    tags: [],
    description: '',
    reference_images: [],
  })

  const resetNewEnv = () =>
    setNewEnv({
      name: '',
      category: 'indoor',
      tags: [],
      description: '',
      reference_images: [],
    })

  const load = useCallback(async () => {
    try {
      setLoading(true)
      const res = await storyStructureAPI.listEnvironments()
      if (res.success && res.data) {
        setList(res.data)
      } else {
        showAlert({ message: res.error || '加载环境失败', variant: 'error' })
      }
    } catch (e) {
      console.error(e)
      showAlert({ message: '加载环境失败', variant: 'error' })
    } finally {
      setLoading(false)
    }
  }, [showAlert])

  useEffect(() => {
    void load()
  }, [load])

  const handleCreate = async (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!newEnv.name.trim()) {
      showAlert({ message: '请填写名称', variant: 'warning' })
      return
    }
    try {
      setCreating(true)
      const payload: EnvironmentCreate = {
        name: newEnv.name.trim(),
        category: newEnv.category || undefined,
        tags: newEnv.tags?.filter(Boolean),
        description: newEnv.description || undefined,
        reference_images: newEnv.reference_images?.filter(Boolean),
        metadata: newEnv.metadata,
      }
      const res = await storyStructureAPI.createEnvironment(payload)
      if (res.success && res.data) {
        setList(prev => [res.data as Environment, ...prev])
        resetNewEnv()
        setShowCreateForm(false)
        showAlert({ message: '创建成功', variant: 'success' })
      } else {
        showAlert({ message: res.error || '创建失败', variant: 'error' })
      }
    } catch (e) {
      console.error(e)
      showAlert({ message: '创建失败', variant: 'error' })
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (id: number) => {
    showAlert({
      title: '确认删除环境',
      message: '删除后引用该环境的场景将失去关联，确定删除吗？',
      variant: 'warning',
      confirmText: '删除',
      onConfirm: async () => {
        try {
          const res = await storyStructureAPI.deleteEnvironment(id)
          if (res.success) {
            setList(prev => prev.filter(item => item.id !== id))
            showAlert({ message: '删除成功', variant: 'success' })
          } else {
            showAlert({ message: res.error || '删除失败', variant: 'error' })
          }
        } catch (e) {
          console.error(e)
          showAlert({ message: '删除失败', variant: 'error' })
        }
      },
    })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation title="环境资产管理" />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">环境资产</h2>
            <p className="text-sm text-gray-500">列表仅展示概要信息，图片在详情内管理</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => setShowCreateForm(true)}
              className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-2 rounded-lg hover:from-blue-700 hover:to-purple-700 shadow"
            >
              创建环境资产
            </button>
            <button
              onClick={() => void load()}
              className="border border-gray-300 px-4 py-2 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              刷新列表
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">环境列表</h2>
            <button onClick={() => void load()} className="text-blue-600 hover:text-blue-800 text-sm">刷新</button>
          </div>
          {loading ? (
            <div className="py-8 text-center text-gray-500">加载中...</div>
          ) : list.length === 0 ? (
            <div className="py-8 text-center text-gray-500">暂无环境，请先创建。</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {list.map(env => (
                <div key={env.id} className="border rounded p-4 hover:shadow-sm space-y-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-semibold text-gray-900">{env.name}</div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => router.push(`/environments/${env.id}`)}
                        className="text-blue-600 hover:text-blue-800 text-xs"
                      >
                        管理图片
                      </button>
                      <button
                        onClick={() => handleDelete(env.id)}
                        className="text-red-600 hover:text-red-800 text-xs"
                      >
                        删除
                      </button>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 mb-2">类别：{env.category || '未指定'}</div>
                  {env.tags && env.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      {env.tags.map(tag => (
                        <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-xs">{tag}</span>
                      ))}
                    </div>
                  )}
                  {env.description && (
                    <p className="text-sm text-gray-700 line-clamp-3 mb-2">{env.description}</p>
                  )}
                  <div className="text-xs text-gray-400 mt-1">
                    创建于 {new Date(env.created_at).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <CreationOverlay
          open={showCreateForm}
          title="创建环境资产"
          subtitle="同一交互样式下快速补充环境基础信息并提交"
          onClose={() => {
            setShowCreateForm(false)
            resetNewEnv()
          }}
          icon={
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7h18M3 12h18M3 17h18" />
            </svg>
          }
        >
          <form onSubmit={handleCreate} className="space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">名称 *</label>
                <input
                  type="text"
                  value={newEnv.name}
                  onChange={e => setNewEnv(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border rounded"
                  placeholder="如：办公室、校园、商场"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">类别</label>
                <select
                  value={newEnv.category}
                  onChange={e => setNewEnv(prev => ({ ...prev, category: e.target.value }))}
                  className="w-full px-3 py-2 border rounded"
                >
                  <option value="indoor">室内</option>
                  <option value="outdoor">室外</option>
                  <option value="other">其它</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">标签（逗号分隔）</label>
                <input
                  type="text"
                  value={(newEnv.tags || []).join(', ')}
                  onChange={e => setNewEnv(prev => ({ ...prev, tags: e.target.value.split(',').map(t => t.trim()).filter(Boolean) }))}
                  className="w-full px-3 py-2 border rounded"
                  placeholder="现代, 写字楼, 开放式"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">参考图 URL（逗号分隔）</label>
                <input
                  type="text"
                  value={(newEnv.reference_images || []).join(', ')}
                  onChange={e => setNewEnv(prev => ({ ...prev, reference_images: e.target.value.split(',').map(t => t.trim()).filter(Boolean) }))}
                  className="w-full px-3 py-2 border rounded"
                  placeholder="http://.../bg1.png, http://.../bg2.png"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
              <textarea
                value={newEnv.description || ''}
                onChange={e => setNewEnv(prev => ({ ...prev, description: e.target.value }))}
                className="w-full px-3 py-2 border rounded"
                rows={3}
                placeholder="简述环境特点、光线、风格等"
              />
            </div>

            <div className="flex justify-end gap-3 border-t pt-4">
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(false)
                  resetNewEnv()
                }}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
              >
                取消
              </button>
              <button
                type="submit"
                disabled={creating}
                className="px-4 py-2 rounded bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 disabled:opacity-50"
              >
                {creating ? '创建中...' : '创建环境'}
              </button>
            </div>
          </form>
        </CreationOverlay>
      </main>
    </div>
  )
}

export default function EnvironmentsPage() {
  return (
    <AuthGuard>
      <EnvironmentsPageContent />
    </AuthGuard>
  )
}
