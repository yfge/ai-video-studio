'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'

import { GenerationAuditWarnings } from '@/components/shared'
import { useAlertModal } from '@/components/shared/modals'
import { storyStructureAPI, type Environment } from '@/utils/api'

import { EnvironmentDetailHeader } from './EnvironmentDetailHeader'
import { EnvironmentHeader } from './EnvironmentHeader'
import { EnvironmentImagesPanel } from './EnvironmentImagesPanel'
import { EnvironmentSidePanel } from './EnvironmentSidePanel'
import { EnvironmentVariantModal } from './EnvironmentVariantModal'
import type { EnvironmentImage } from './types'

export function EnvironmentDetailView() {
  const params = useParams()
  const router = useRouter()
  const { showAlert } = useAlertModal()
  const envKey = params?.id?.toString() || ''

  const [env, setEnv] = useState<Environment | null>(null)
  const [images, setImages] = useState<EnvironmentImage[]>([])
  const [loading, setLoading] = useState(true)
  const [variantTarget, setVariantTarget] = useState<EnvironmentImage | null>(null)
  const [editingMeta, setEditingMeta] = useState(false)
  const [savingMeta, setSavingMeta] = useState(false)
  const [metaForm, setMetaForm] = useState({
    category: '',
    tags: [] as string[],
    description: '',
  })

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
        showAlert({
          message: envRes.error || '加载环境失败',
          variant: 'error',
        })
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

  useEffect(() => {
    if (!env || editingMeta) return
    setMetaForm({
      category: env.category || '',
      tags: env.tags || [],
      description: env.description || '',
    })
  }, [env, editingMeta])

  const handleDeleteImage = useCallback(
    (url: string) => {
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
    },
    [envKey, showAlert],
  )

  const handleAddTag = useCallback((tag: string) => {
    const trimmed = tag.trim()
    if (!trimmed) return
    setMetaForm((prev) =>
      prev.tags.includes(trimmed) ? prev : { ...prev, tags: [...prev.tags, trimmed] }
    )
  }, [])

  const handleRemoveTag = useCallback((tag: string) => {
    setMetaForm((prev) => ({ ...prev, tags: prev.tags.filter((item) => item !== tag) }))
  }, [])

  const handleCancelMeta = useCallback(() => {
    if (env) {
      setMetaForm({
        category: env.category || '',
        tags: env.tags || [],
        description: env.description || '',
      })
    }
    setEditingMeta(false)
  }, [env])

  const handleSaveMeta = useCallback(async () => {
    if (!envKey) return
    try {
      setSavingMeta(true)
      const res = await storyStructureAPI.updateEnvironment(envKey, {
        category: metaForm.category,
        tags: metaForm.tags,
        description: metaForm.description,
      })
      if (res.success && res.data) {
        setEnv(res.data)
        setEditingMeta(false)
        showAlert({ message: '环境信息已更新', variant: 'success' })
      } else {
        showAlert({ message: res.error || '更新失败', variant: 'error' })
      }
    } catch (error) {
      console.error(error)
      showAlert({ message: '更新失败', variant: 'error' })
    } finally {
      setSavingMeta(false)
    }
  }, [envKey, metaForm.category, metaForm.description, metaForm.tags, showAlert])

  const handleImageUploaded = useCallback((url: string) => {
    setImages((prev) => [{ url }, ...prev])
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex justify-center items-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
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

  const envMeta = (env.metadata ?? {}) as Record<string, unknown>
  const lastTextToImageWarnings = (
    envMeta['last_text_to_image_generation'] as Record<string, unknown> | undefined
  )?.['audit_warnings']
  const lastImageToImageWarnings = (
    envMeta['last_image_to_image_generation'] as Record<string, unknown> | undefined
  )?.['audit_warnings']

  return (
    <div className="min-h-screen bg-gray-50">
      <EnvironmentDetailHeader
        editing={editingMeta}
        saving={savingMeta}
        onEdit={() => setEditingMeta(true)}
        onCancel={handleCancelMeta}
        onSave={handleSaveMeta}
      />
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <div className="space-y-3">
          <GenerationAuditWarnings title="环境文生图提示" warnings={lastTextToImageWarnings} />
          <GenerationAuditWarnings title="环境图生图提示" warnings={lastImageToImageWarnings} />
        </div>
        <div className="bg-white shadow-sm ring-1 ring-gray-200 rounded-2xl overflow-hidden">
          <EnvironmentHeader
            env={env}
            editing={editingMeta}
            form={metaForm}
            setForm={setMetaForm}
            addTag={handleAddTag}
            removeTag={handleRemoveTag}
          />
        </div>

        <div className="bg-white shadow-sm ring-1 ring-gray-200 rounded-2xl overflow-hidden">
          <div className="p-6 sm:p-8 border-b border-gray-100">
            <EnvironmentSidePanel
              envKey={envKey}
              onImageUploaded={handleImageUploaded}
              variant="embedded"
            />
          </div>
          <div className="p-6 sm:p-8">
            <EnvironmentImagesPanel
              envName={env.name}
              images={images}
              imageSrc={imageSrc}
              onImg2Img={(image) => setVariantTarget(image)}
              onDelete={handleDeleteImage}
              variant="embedded"
            />
          </div>
        </div>
      </main>
      <EnvironmentVariantModal
        envKey={envKey}
        env={env}
        target={variantTarget}
        imageSrc={imageSrc}
        onClose={() => setVariantTarget(null)}
      />
    </div>
  )
}
