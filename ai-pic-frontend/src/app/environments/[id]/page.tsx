'use client'

import Image from 'next/image'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import AuthGuard from '@/components/AuthGuard'
import Navigation from '@/components/Navigation'
import { useAlertModal } from '@/components/AlertModalProvider'
import { ImageToImageModal } from '@/components/ImageToImageModal'
import { storyStructureAPI, AIModelType, type Environment } from '@/utils/api'

interface EnvironmentImage {
  url: string
}

function EnvironmentDetailContent() {
  const params = useParams()
  const router = useRouter()
  const { showAlert } = useAlertModal()
  const envKey = params?.id?.toString() || ''

  const [env, setEnv] = useState<Environment | null>(null)
  const [images, setImages] = useState<EnvironmentImage[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [prompt, setPrompt] = useState('')
  const [generating, setGenerating] = useState(false)
  const [variantTarget, setVariantTarget] = useState<EnvironmentImage | null>(null)
  const [variantPrompt, setVariantPrompt] = useState('')
  const [variantOpen, setVariantOpen] = useState(false)
  const [variantSubmitting, setVariantSubmitting] = useState(false)

  const apiBase = useMemo(
    () => (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, ''),
    [],
  )

  const imageSrc = useCallback(
    (url: string) => {
      if (!url) return ''
      if (url.startsWith('http')) return url
      return `${apiBase}${url.startsWith('/') ? url : `/${url}`}`
    },
    [apiBase],
  )

  const load = useCallback(async () => {
    if (!envKey) return
    try {
      setLoading(true)
      const [envRes, imgRes] = await Promise.all([
        storyStructureAPI.getEnvironment(envKey),
        storyStructureAPI.listEnvironmentImages(envKey),
      ])
      if (envRes.success && envRes.data) {
        setEnv(envRes.data)
      } else {
        showAlert({ message: envRes.error || '加载环境失败', variant: 'error' })
      }
      if (imgRes.success && imgRes.data) {
        setImages(imgRes.data.images || [])
      } else {
        setImages([])
      }
    } catch (error) {
      console.error(error)
      showAlert({ message: '加载环境详情失败', variant: 'error' })
    } finally {
      setLoading(false)
    }
  }, [envKey, showAlert])

  useEffect(() => {
    void load()
  }, [load])

  const handleUpload = async () => {
    if (!selectedFile || !envKey) {
      showAlert({ message: '请选择图片文件', variant: 'warning' })
      return
    }
    try {
      setUploading(true)
      const res = await storyStructureAPI.uploadEnvironmentImage(envKey, selectedFile)
      if (res.success && res.data) {
        const uploaded = res.data
        setImages(prev => [{ url: uploaded.url }, ...prev])
        setSelectedFile(null)
        showAlert({ message: '上传成功', variant: 'success' })
      } else {
        showAlert({ message: res.error || '上传失败', variant: 'error' })
      }
    } catch (error) {
      console.error(error)
      showAlert({ message: '上传失败', variant: 'error' })
    } finally {
      setUploading(false)
    }
  }

  const handleDeleteImage = async (url: string) => {
    if (!envKey) return
    showAlert({
      title: '确认删除',
      message: '确定要删除该参考图吗？',
      variant: 'warning',
      confirmText: '删除',
      onConfirm: async () => {
        const res = await storyStructureAPI.deleteEnvironmentImage(envKey, url)
        if (res.success && res.data) {
          setImages(res.data.images ?? [])
          showAlert({ message: '删除成功', variant: 'success' })
        } else {
          showAlert({ message: res.error || '删除失败', variant: 'error' })
        }
      },
    })
  }

  const handleGenerate = async () => {
    if (!envKey) return
    try {
      setGenerating(true)
      const res = await storyStructureAPI.generateEnvironmentImagesAsync(envKey, {
        prompt: prompt || undefined,
      })
      if (res.success) {
        showAlert({
          title: '已创建环境图生成任务',
          message: '任务将在后台执行，完成后刷新本页查看新图片。',
          variant: 'success',
        })
      } else {
        showAlert({ message: res.error || '生成失败', variant: 'error' })
      }
    } catch (error) {
      console.error(error)
      showAlert({ message: '生成失败', variant: 'error' })
    } finally {
      setGenerating(false)
    }
  }

  const openVariant = (image: EnvironmentImage) => {
    setVariantTarget(image)
    setVariantPrompt(env?.description || env?.name || '基于该环境参考图生成一致风格的变体')
    setVariantOpen(true)
  }

  const handleSubmitVariant = async (payload: {
    prompt: string
    model?: string
    count: number
    size?: string
    style?: string
    style_preset_id?: string
    style_spec?: Record<string, unknown>
    referenceImages: string[]
  }) => {
    if (!envKey || !variantTarget) return
    try {
      setVariantSubmitting(true)
      const res = await storyStructureAPI.generateEnvironmentImageVariantsAsync(envKey, {
        base_image: variantTarget.url,
        prompt: payload.prompt,
        model: payload.model,
        count: payload.count,
        size: payload.size,
        style: payload.style,
        style_preset_id: payload.style_preset_id,
        style_spec: payload.style_spec,
        reference_images: payload.referenceImages,
      })
      if (res.success) {
        showAlert({
          title: '已创建环境图变体任务',
          message: '任务将在后台生成，完成后刷新即可看到新图片。',
          variant: 'success',
        })
        setVariantOpen(false)
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex justify-center items-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!env) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <p className="text-gray-600 mb-4">环境不存在或已删除。</p>
        <button
          onClick={() => router.push('/environments')}
          className="px-4 py-2 bg-blue-600 text-white rounded"
        >
          返回列表
        </button>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation title="环境详情" />
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{env.name}</h1>
            <p className="text-sm text-gray-500 mt-1">
              类别：{env.category || '未指定'} · 创建于 {new Date(env.created_at).toLocaleString()}
            </p>
            {env.tags && env.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {env.tags.map(tag => (
                  <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-xs">{tag}</span>
                ))}
              </div>
            )}
            {env.description && (
              <p className="mt-3 text-gray-700 whitespace-pre-wrap">{env.description}</p>
            )}
          </div>
          <button
            onClick={() => router.push('/environments')}
            className="text-blue-600 hover:text-blue-800"
          >
            返回列表
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow p-4 space-y-3 lg:col-span-2">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">参考图</h3>
              <span className="text-sm text-gray-500">共 {images.length} 张</span>
            </div>
            {images.length === 0 ? (
              <div className="py-8 text-center text-gray-500">
                还没有参考图，上传或生成一张试试。
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                {images.map(img => {
                  const src = imageSrc(img.url)
                  return (
                    <div key={img.url} className="relative rounded border bg-gray-50 overflow-hidden">
                      {src ? (
                        <Image
                          src={src}
                          alt={env.name}
                          width={300}
                          height={300}
                          className="object-cover w-full h-full"
                          unoptimized
                        />
                      ) : (
                        <div className="h-32 flex items-center justify-center text-gray-400 text-sm">无效图片</div>
                      )}
                      <div className="absolute inset-0 flex items-start justify-end gap-2 p-2">
                        <button
                          onClick={() => openVariant(img)}
                          className="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700"
                        >
                          图生图
                        </button>
                        <button
                          onClick={() => handleDeleteImage(img.url)}
                          className="rounded bg-black/60 px-2 py-1 text-xs text-white hover:bg-black/80"
                        >
                          删除
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          <div className="bg-white rounded-lg shadow p-4 space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">上传参考图</h3>
              <p className="text-sm text-gray-500">支持常见图片格式，自动走 OSS 持久化。</p>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                className="mt-2 w-full text-sm"
              />
              <button
                onClick={handleUpload}
                disabled={uploading || !selectedFile}
                className="mt-3 w-full rounded bg-blue-600 px-3 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {uploading ? '上传中...' : '上传图片'}
              </button>
            </div>
            <div className="border-t pt-3">
              <h3 className="text-lg font-semibold text-gray-900">AI 生成参考图</h3>
              <p className="text-sm text-gray-500">可选提示词，不填则按环境描述生成。</p>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={3}
                className="w-full rounded border px-3 py-2 text-sm"
                placeholder="可选：补充想要的风格/光影/构图"
              />
              <button
                onClick={handleGenerate}
                disabled={generating}
                className="mt-3 w-full rounded bg-green-600 px-3 py-2 text-white hover:bg-green-700 disabled:opacity-50"
              >
                {generating ? '提交任务中...' : '创建生成任务'}
              </button>
            </div>
          </div>
        </div>
      </main>
      <ImageToImageModal
        open={variantOpen && !!variantTarget}
        onClose={() => {
          setVariantOpen(false)
          setVariantTarget(null)
        }}
        title="环境图生图"
        description="参考当前环境图，调整模型与参数后提交生成变体。"
        referenceSections={
          variantTarget
            ? [{ title: '参考图', images: [imageSrc(variantTarget.url)] }]
            : []
        }
        defaultSelected={
          variantTarget ? [imageSrc(variantTarget.url)] : []
        }
        defaultPrompt={variantPrompt}
        defaultCount={1}
        modelType={AIModelType.ImageToImage}
        modelCacheKey="environment-img2img"
        submitting={variantSubmitting}
        onSubmit={handleSubmitVariant}
      />
    </div>
  )
}

export default function EnvironmentDetailPage() {
  return (
    <AuthGuard>
      <EnvironmentDetailContent />
    </AuthGuard>
  )
}
