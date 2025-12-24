'use client'

import { useState } from 'react'

import { useAlertModal } from '@/components/shared/modals'
import { storyStructureAPI } from '@/utils/api'

import { EnvironmentGenerationFields } from './EnvironmentGenerationFields'
import { EMPTY_GENERATION, type GenerationFormState } from './types'

interface EnvironmentSidePanelProps {
  envKey: string
  onImageUploaded: (imageUrl: string) => void
  variant?: 'card' | 'embedded'
}

export function EnvironmentSidePanel({
  envKey,
  onImageUploaded,
  variant = 'card',
}: EnvironmentSidePanelProps) {
  const { showAlert } = useAlertModal()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [generation, setGeneration] = useState<GenerationFormState>({
    ...EMPTY_GENERATION,
    enabled: true,
  })
  const [generating, setGenerating] = useState(false)

  const handleUpload = async () => {
    if (!selectedFile || !envKey) {
      showAlert({ message: '请选择图片文件', variant: 'warning' })
      return
    }
    try {
      setUploading(true)
      const res = await storyStructureAPI.uploadEnvironmentImage(envKey, selectedFile)
      if (res.success && res.data) {
        onImageUploaded(res.data.url)
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

  const handleGenerate = async () => {
    if (!envKey) {
      showAlert({ message: '环境信息缺失', variant: 'warning' })
      return
    }
    try {
      setGenerating(true)
        const res = await storyStructureAPI.generateEnvironmentImagesAsync(envKey, {
          prompt: generation.prompt || undefined,
          model: generation.model || undefined,
          count: generation.count,
          size: generation.size || undefined,
          aspect_ratio: generation.aspect_ratio || undefined,
          style: generation.style || undefined,
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

  const containerClassName =
    variant === 'embedded'
      ? 'space-y-5'
      : 'bg-white rounded-2xl shadow-sm ring-1 ring-gray-200 p-6 space-y-5'

  return (
    <div className={containerClassName}>
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

      <div className="border-t border-gray-100 pt-4 space-y-3">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">AI 生成参考图</h3>
          <p className="text-sm text-gray-500">可选提示词，不填则按环境描述生成。</p>
        </div>
        <EnvironmentGenerationFields
          generation={generation}
          setGeneration={setGeneration}
          showToggle={false}
          withDivider={false}
        />
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="w-full rounded bg-green-600 px-3 py-2 text-white hover:bg-green-700 disabled:opacity-50"
        >
          {generating ? '提交任务中...' : '创建生成任务'}
        </button>
      </div>
    </div>
  )
}
