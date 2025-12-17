"use client"

import Image from "next/image"
import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import AuthGuard from '@/components/AuthGuard'
import Navigation from '@/components/Navigation'
import { StyleSpecAdvancedPanel, type StyleSpecField } from '@/components/StyleSpecAdvancedPanel'
import {
  storyStructureAPI,
  AIModelType,
  type EnvironmentCreate,
  type Environment,
  type StyleSpec,
} from '@/utils/api'
import { useAlertModal } from '@/components/AlertModalProvider'
import { ImageToImageModal } from '@/components/ImageToImageModal'
import { MultiModelSelector } from '@/components/MultiModelSelector'
import { ImagePreviewModal } from '@/components/ImagePreviewModal'
import { useStylePresets } from '@/hooks/useStylePresets'
import { CreationOverlay } from '@/components/CreationOverlay'

const ENV_STYLE_SPEC_FIELDS: StyleSpecField[] = [
  { key: 'style_universe', label: '世界观 / 画风体系' },
  { key: 'lighting_style', label: '阴影与光影' },
  { key: 'color_mood', label: '色彩情绪' },
  { key: 'background_detail_level', label: '背景复杂度' },
  { key: 'composition_style', label: '构图与画面密度' },
]

function EnvironmentsPageContent() {
  const { showAlert } = useAlertModal()
  const [list, setList] = useState<Environment[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [creating, setCreating] = useState(false)
  const [generating, setGenerating] = useState<Record<number, boolean>>({})
  const [selectedModels, setSelectedModels] = useState<Record<number, string>>({})
  const [selectedStylePresets, setSelectedStylePresets] = useState<
    Record<number, string>
  >({})
  const [selectedStyleSpecs, setSelectedStyleSpecs] = useState<Record<number, StyleSpec>>({})
  const { presets: stylePresets } = useStylePresets()
  const [variantTarget, setVariantTarget] = useState<{
    env: Environment
    url: string
    displayUrl: string
    modelHint?: string
    stylePresetHint?: string
    styleSpecHint?: StyleSpec
  } | null>(null)
  const [variantModalOpen, setVariantModalOpen] = useState(false)
  const [variantPrompt, setVariantPrompt] = useState('')
  const [variantSubmitting, setVariantSubmitting] = useState(false)
  const [preview, setPreview] = useState<{ src: string; alt?: string; description?: string } | null>(null)
  const [newEnv, setNewEnv] = useState<EnvironmentCreate>({
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

  const apiBase = useMemo(
    () => (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, ''),
    [],
  )

  const resetNewEnv = () =>
    setNewEnv({
      name: '',
      category: 'indoor',
      tags: [],
      description: '',
      reference_images: [],
    })

  const imageSrc = useCallback(
    (url: string) => {
      if (!url) return ''
      if (url.startsWith('http')) return url
      return `${apiBase}${url.startsWith('/') ? url : `/${url}`}`
    },
    [apiBase]
  )

  const handleCreate = async (e?: FormEvent) => {
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

  const handleGenerateImage = async (env: Environment, options: { prompt?: string; model?: string; size?: string }) => {
    setGenerating(prev => ({ ...prev, [env.id]: true }))
    try {
      const selectedSpec = selectedStyleSpecs[env.id]
      const payload = {
        prompt: options.prompt || env.description || env.name,
        model: options.model,
        size: options.size,
        count: 1,
        style_preset_id: selectedStylePresets[env.id] || undefined,
        style_spec: selectedSpec && Object.keys(selectedSpec).length > 0 ? selectedSpec : undefined,
      }
      const res = await storyStructureAPI.generateEnvironmentImagesAsync(env.id, payload)
      if (res.success) {
        showAlert({
          title: '已创建环境图生成任务',
          message: '任务会在后台异步执行，生成完成后刷新环境列表即可看到新参考图。',
          variant: 'success',
        })
      } else {
        showAlert({ message: res.error || '生成失败', variant: 'error' })
      }
    } catch (error) {
      console.error(error)
      showAlert({ message: '生成失败', variant: 'error' })
    } finally {
      setGenerating(prev => ({ ...prev, [env.id]: false }))
    }
  }

  const openVariantModal = (env: Environment, url: string) => {
    setVariantTarget({
      env,
      url,
      displayUrl: imageSrc(url),
      modelHint: selectedModels[env.id],
      stylePresetHint: selectedStylePresets[env.id],
      styleSpecHint: selectedStyleSpecs[env.id],
    })
    setVariantPrompt(env.description || env.name || '基于此环境图生成风格一致的变体')
    setVariantModalOpen(true)
  }

  const handleGenerateVariant = async (payload: {
    prompt: string
    model?: string
    count: number
    size?: string
    style?: string
    style_preset_id?: string
    style_spec?: StyleSpec
    referenceImages: string[]
  }) => {
    if (!variantTarget) return
    setVariantSubmitting(true)
    try {
      const res = await storyStructureAPI.generateEnvironmentImageVariantsAsync(variantTarget.env.id, {
        base_image: variantTarget.url,
        prompt: payload.prompt || variantPrompt,
        model: payload.model || variantTarget.modelHint,
        size: payload.size,
        count: payload.count,
        style: payload.style,
        style_preset_id: payload.style_preset_id || variantTarget.stylePresetHint,
        style_spec: payload.style_spec,
        reference_images: payload.referenceImages,
      })
      if (res.success) {
        showAlert({
          title: '已创建环境图变体任务',
          message: '任务会在后台异步执行，生成完成后刷新环境列表即可看到新参考图。',
          variant: 'success',
        })
        setVariantModalOpen(false)
        setVariantTarget(null)
      } else {
        showAlert({ message: res.error || '变体生成失败', variant: 'error' })
      }
    } catch (error) {
      console.error(error)
      showAlert({ message: '变体生成失败', variant: 'error' })
    } finally {
      setVariantSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation title="环境资产管理" />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">环境资产</h2>
            <p className="text-sm text-gray-500">创建与故事/虚拟IP一致的统一创建体验</p>
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
                    <button
                      onClick={() => handleDelete(env.id)}
                      className="text-red-600 hover:text-red-800 text-xs"
                    >删除</button>
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
                  <div className="text-xs text-gray-500">参考图：{env.reference_images?.length || 0} 张</div>
                  {env.reference_images && env.reference_images.length > 0 && (
                    <div className="mt-2 grid grid-cols-2 gap-2">
                      {env.reference_images.map(url => (
                        <div key={url} className="relative group rounded overflow-hidden border h-24 bg-gray-50">
                          <Image
                            src={imageSrc(url)}
                            alt={env.name}
                            fill
                            sizes="100%"
                            className="object-contain p-1 cursor-zoom-in"
                            unoptimized
                            onClick={() =>
                              setPreview({
                                src: imageSrc(url),
                                alt: env.name,
                                description: `环境参考图 · ${env.name}`,
                              })
                            }
                          />
                          <div className="absolute inset-0 hidden items-center justify-center gap-2 bg-black/40 text-white text-xs group-hover:flex">
                            <button
                              type="button"
                              className="rounded bg-white/80 px-2 py-1 text-gray-800 hover:bg-white"
                              onClick={() =>
                                setPreview({
                                  src: imageSrc(url),
                                  alt: env.name,
                                  description: `环境参考图 · ${env.name}`,
                                })
                              }
                            >
                              预览
                            </button>
                            <button
                              type="button"
                              className="rounded bg-white/80 px-2 py-1 text-gray-800 hover:bg-white"
                              onClick={() => openVariantModal(env, url)}
                            >
                              变体
                            </button>
                            <button
                              type="button"
                              className="rounded bg-red-500 px-2 py-1 text-white hover:bg-red-600"
                              onClick={() => storyStructureAPI.deleteEnvironmentImage(env.id, url).then(res => {
                                if (res.success) {
                                  showAlert({ message: '已删除参考图', variant: 'success' })
                                  void load()
                                } else {
                                  showAlert({ message: res.error || '删除失败', variant: 'error' })
                                }
                              })}
                            >
                              删除
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                    <div className="rounded border border-dashed border-gray-200 p-3 text-xs text-gray-600 space-y-2">
                      <div className="font-semibold text-gray-700">AI 生成参考图</div>
                      <MultiModelSelector
                        value={selectedModels[env.id] ? [selectedModels[env.id]] : []}
                        onChange={ids => setSelectedModels(prev => ({ ...prev, [env.id]: ids[0] || '' }))}
                        modelType="image"
                        helperText="默认使用环境描述作为提示词"
                        allowAuto={true}
                        autoLabel="自动选择"
                        multiple={false}
                        className="text-sm"
                      />
                      <div className="space-y-1">
                        <div className="text-xs text-gray-500">风格预设</div>
                        <select
                          value={selectedStylePresets[env.id] || ''}
                          onChange={e =>
                            setSelectedStylePresets(prev => ({
                              ...prev,
                              [env.id]: e.target.value,
                            }))
                          }
                          className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        >
                          <option value="">（不使用预设）</option>
                          {stylePresets.map(preset => (
                            <option key={preset.preset_id} value={preset.preset_id}>
                              {preset.label || preset.preset_id}
                            </option>
                          ))}
                        </select>
                      </div>
                      <StyleSpecAdvancedPanel
                        fields={ENV_STYLE_SPEC_FIELDS}
                        value={selectedStyleSpecs[env.id] || {}}
                        onChange={next =>
                          setSelectedStyleSpecs(prev => ({
                            ...prev,
                            [env.id]: next,
                          }))
                        }
                      />
                      <button
                      onClick={() => handleGenerateImage(env, { prompt: env.description || env.name, model: selectedModels[env.id] })}
                      disabled={generating[env.id]}
                      className="w-full rounded bg-blue-600 px-3 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
                    >
                      {generating[env.id] ? '生成中...' : '一键生成参考图'}
                    </button>
                  </div>
                  {(() => {
                    const meta = (env.metadata || {}) as Record<string, unknown>
                    const lastT2IRaw = meta['last_text_to_image_generation']
                    const lastI2IRaw = meta['last_image_to_image_generation']

                    const asRecord = (input: unknown): Record<string, unknown> | null => {
                      if (!input || typeof input !== 'object') return null
                      return input as Record<string, unknown>
                    }

                    const readString = (
                      record: Record<string, unknown> | null,
                      key: string,
                    ): string | null => {
                      const value = record ? record[key] : undefined
                      return typeof value === 'string' && value.trim() ? value : null
                    }

                    const lastT2I = asRecord(lastT2IRaw)
                    const lastI2I = asRecord(lastI2IRaw)
                    if (!lastT2I && !lastI2I) return null
                    return (
                      <details className="rounded border border-gray-200 bg-gray-50 p-2 text-[11px] text-gray-700">
                        <summary className="cursor-pointer select-none text-xs font-medium text-gray-700">
                          上次生成风格信息
                        </summary>
                        {lastT2I ? (
                          <div className="mt-2">
                            <div className="font-medium text-gray-700">文生图</div>
                            <div className="mt-1">
                              preset: {readString(lastT2I, 'style_preset_id') || '—'} ｜ provider:{' '}
                              {readString(lastT2I, 'provider') || '—'} ｜ model:{' '}
                              {readString(lastT2I, 'model') || '—'}
                            </div>
                            <div className="mt-1 break-all">
                              spec: {JSON.stringify(lastT2I['style_spec'] ?? null)}
                            </div>
                            <div className="mt-1 break-all">
                              resolution: {JSON.stringify(lastT2I['style_spec_resolution'] ?? null)}
                            </div>
                          </div>
                        ) : null}
                        {lastI2I ? (
                          <div className="mt-3">
                            <div className="font-medium text-gray-700">图生图</div>
                            <div className="mt-1">
                              preset: {readString(lastI2I, 'style_preset_id') || '—'} ｜ provider:{' '}
                              {readString(lastI2I, 'provider') || '—'} ｜ model:{' '}
                              {readString(lastI2I, 'model') || '—'}
                            </div>
                            <div className="mt-1 break-all">
                              spec: {JSON.stringify(lastI2I['style_spec'] ?? null)}
                            </div>
                            <div className="mt-1 break-all">
                              resolution: {JSON.stringify(lastI2I['style_spec_resolution'] ?? null)}
                            </div>
                          </div>
                        ) : null}
                      </details>
                    )
                  })()}
                  <div className="text-xs text-gray-400 mt-1">
                    创建于 {new Date(env.created_at).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <ImageToImageModal
          open={variantModalOpen && !!variantTarget}
          onClose={() => {
            setVariantModalOpen(false)
            setVariantTarget(null)
          }}
          title="环境图生图"
          description="参考图与提示词已展示，可调整模型、分辨率与生成张数后提交任务。"
          referenceSections={
            variantTarget?.displayUrl
              ? [{ title: '参考图', images: [variantTarget.displayUrl] }]
              : []
          }
          defaultSelected={variantTarget?.displayUrl ? [variantTarget.displayUrl] : []}
          lockSelection
          defaultPrompt={variantPrompt}
          defaultModel={variantTarget?.modelHint || ''}
          defaultCount={1}
          defaultStylePresetId={variantTarget?.stylePresetHint || ''}
          defaultStyleSpec={variantTarget?.styleSpecHint || {}}
          styleSpecFields={ENV_STYLE_SPEC_FIELDS}
          modelType={AIModelType.ImageToImage}
          modelCacheKey="environment-img2img"
          submitting={variantSubmitting}
          onSubmit={handleGenerateVariant}
        />

        <ImagePreviewModal
          open={!!preview}
          src={preview?.src || ''}
          alt={preview?.alt}
          description={preview?.description}
          onClose={() => setPreview(null)}
        />

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
