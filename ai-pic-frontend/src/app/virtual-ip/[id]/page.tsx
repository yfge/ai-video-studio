'use client'

import Image from 'next/image'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { apiClient, virtualIPAPI, voiceAPI, VirtualIP, VoiceConfig, VoiceEnums, VoiceList, VoiceItem } from '@/utils/api'
import { useAlertModal } from '@/components/shared/modals/AlertModalProvider'

export default function VirtualIPDetail() {
  const params = useParams()
  const router = useRouter()
  const { showAlert } = useAlertModal()
  const [virtualIP, setVirtualIP] = useState<VirtualIP | null>(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState({
    name: '',
    description: '',
    tags: [] as string[],
    background_story: ''
  })
  const [voiceEnums, setVoiceEnums] = useState<VoiceEnums | null>(null)
  const [voiceList, setVoiceList] = useState<VoiceList | null>(null)
  const [voiceTypeFilter, setVoiceTypeFilter] = useState('system')
  const [voiceSettings, setVoiceSettings] = useState<VoiceConfig>({
    provider: undefined,
    model: undefined,
    voice_type: 'system',
    voice_id: undefined
  })
  const [voicePreviewText, setVoicePreviewText] = useState('')
  const [voiceLoading, setVoiceLoading] = useState(false)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [previewAudioUrl, setPreviewAudioUrl] = useState<string | null>(null)

  const ipKey = params?.id?.toString() || ''

  const buildDefaultVoiceSettings = (enums: VoiceEnums): VoiceConfig => {
    const provider = enums.providers?.[0]?.value
    const model = enums.defaults?.tts_model || enums.tts_models?.[0]?.value || undefined
    const voice_id = enums.defaults?.voice_id || undefined
    const voice_type = enums.voice_types?.[0]?.value || 'system'
    return {
      provider,
      model,
      voice_type,
      voice_id
    }
  }

  const mergeVoiceSettings = (
    current: VoiceConfig,
    defaults: VoiceConfig,
    incoming?: VoiceConfig
  ): VoiceConfig => ({
    provider: incoming?.provider ?? current.provider ?? defaults.provider,
    model: incoming?.model ?? current.model ?? defaults.model,
    voice_type: incoming?.voice_type ?? current.voice_type ?? defaults.voice_type ?? 'system',
    voice_id: incoming?.voice_id ?? current.voice_id ?? defaults.voice_id,
    display_name: incoming?.display_name ?? current.display_name,
    sample_url: incoming?.sample_url ?? current.sample_url
  })

  const hexToAudioUrl = (hexString: string): string => {
    const bytes = new Uint8Array(hexString.match(/.{1,2}/g)?.map((byte) => parseInt(byte, 16)) || [])
    const blob = new Blob([bytes], { type: 'audio/mpeg' })
    return URL.createObjectURL(blob)
  }

  const fetchVoiceEnums = useCallback(async () => {
    try {
      const res = await voiceAPI.getEnums()
      if (res.success && res.data) {
        setVoiceEnums(res.data)
        // 初始化默认试听文本
        if (!voicePreviewText) {
          setVoicePreviewText('你好，我是你的虚拟角色，很高兴与您相见。')
        }
        // 初始化语音设置
        const defaults = buildDefaultVoiceSettings(res.data)
        setVoiceSettings((prev) => mergeVoiceSettings(prev, defaults))
      }
    } catch (error) {
      console.error('获取语音枚举失败', error)
    }
  }, [voicePreviewText])

  const fetchVoiceList = useCallback(
    async (voiceType: string, provider?: string) => {
      if (!provider) return
      try {
        setVoiceLoading(true)
        const res = await voiceAPI.getVoices({
          voice_type: voiceType,
          provider
        })
        if (res.success && res.data) {
          setVoiceList(res.data)
        }
      } catch (error) {
        console.error('获取音色列表失败', error)
      } finally {
        setVoiceLoading(false)
      }
    },
    []
  )

  // 获取虚拟IP详情
  const fetchVirtualIP = useCallback(async () => {
    try {
      setLoading(true)
      const response = await virtualIPAPI.getVirtualIP(ipKey)
      
      if (response.success && response.data) {
        setVirtualIP(response.data)
        setEditForm({
          name: response.data.name,
          description: response.data.description || '',
          tags: response.data.tags || [],
          background_story: response.data.background_story || ''
        })
        const incomingVoice = response.data.voice_config
        setVoiceSettings((prev) => {
          const enums = voiceEnums
          const defaults = enums ? buildDefaultVoiceSettings(enums) : prev
          return mergeVoiceSettings(prev, defaults, incomingVoice)
        })
        if (!voicePreviewText) {
          setVoicePreviewText(`你好，我是${response.data.name}，很高兴和你见面。`)
        }
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
  }, [ipKey, showAlert, voiceEnums, voicePreviewText])

  // 更新虚拟IP
  const handleUpdateIP = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const identifier = virtualIP?.business_id || ipKey
      const response = await virtualIPAPI.updateVirtualIP(identifier, {
        ...editForm,
        voice_config: voiceSettings
      })
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
  const deleteCurrentVirtualIP = async () => {
    try {
      const identifier = virtualIP?.business_id || ipKey
      const response = await virtualIPAPI.deleteVirtualIP(identifier)
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

  const handleDeleteIP = () => {
    showAlert({
      title: '确认删除虚拟IP',
      message: '确定要删除这个虚拟IP吗？此操作不可恢复！',
      variant: 'warning',
      confirmText: '删除',
      onConfirm: () => {
        void deleteCurrentVirtualIP()
      },
    })
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

  const voiceOptions = useMemo(() => {
    const options: { value: string; label: string }[] = []
    const pushVoices = (items?: VoiceItem[]) => {
      if (!items) return
      items.forEach((item) => {
        if (item?.voice_id) {
          options.push({
            value: item.voice_id,
            label: item.voice_name || item.voice_id
          })
        }
      })
    }

    if (voiceList) {
      if (voiceTypeFilter === 'all') {
        pushVoices(voiceList.system_voice)
        pushVoices(voiceList.voice_cloning)
        pushVoices(voiceList.voice_generation)
      } else if (voiceTypeFilter === 'system') {
        pushVoices(voiceList.system_voice)
      } else if (voiceTypeFilter === 'voice_cloning') {
        pushVoices(voiceList.voice_cloning)
      } else if (voiceTypeFilter === 'voice_generation') {
        pushVoices(voiceList.voice_generation)
      }
    }
    if (!options.length && voiceEnums?.system_voices && voiceTypeFilter !== 'voice_cloning' && voiceTypeFilter !== 'voice_generation') {
      voiceEnums.system_voices.forEach((item) => {
        options.push({
          value: item.value,
          label: item.label_zh || item.label_en || item.value
        })
      })
    }
    return options
  }, [voiceList, voiceTypeFilter, voiceEnums?.system_voices])

  const handlePreviewVoice = async () => {
    // 确保存在模型/音色默认值
    const fallbackModel =
      voiceSettings.model || voiceEnums?.defaults?.tts_model || voiceEnums?.tts_models?.[0]?.value
    const fallbackVoiceId =
      voiceSettings.voice_id || voiceEnums?.defaults?.voice_id || voiceOptions[0]?.value
    const fallbackProvider = voiceSettings.provider || voiceEnums?.providers?.[0]?.value

    if (!fallbackProvider) {
      showAlert({ message: '请先选择语音提供商', variant: 'error' })
      return
    }
    if (!fallbackModel) {
      showAlert({ message: '请先选择语音模型', variant: 'error' })
      return
    }

    if (
      fallbackModel !== voiceSettings.model ||
      fallbackVoiceId !== voiceSettings.voice_id ||
      fallbackProvider !== voiceSettings.provider
    ) {
      setVoiceSettings((prev) => ({
        ...prev,
        provider: fallbackProvider,
        model: fallbackModel,
        voice_id: fallbackVoiceId
      }))
    }

    const text = voicePreviewText || `你好，我是${virtualIP?.name || '角色'}，很高兴见到你。`
    setPreviewLoading(true)
    try {
      const res = await voiceAPI.preview({
        text,
        model: fallbackModel,
        voice_id: fallbackVoiceId,
        provider: fallbackProvider,
        output_format: 'url'
      })
      if (res.success && res.data) {
        const audioUrl =
          res.data.audio_url ||
          (res.data.audio_hex ? hexToAudioUrl(res.data.audio_hex) : null)
        if (audioUrl) {
          if (previewAudioUrl) {
            URL.revokeObjectURL(previewAudioUrl)
          }
          setPreviewAudioUrl(audioUrl)
        }
        showAlert({ message: '试听已生成', variant: 'success' })
      } else {
        showAlert({ message: `试听失败: ${res.error || '未知错误'}`, variant: 'error' })
      }
    } catch (error) {
      console.error('试听失败', error)
      showAlert({ message: '试听失败，请重试', variant: 'error' })
    } finally {
      setPreviewLoading(false)
    }
  }

  useEffect(() => {
    apiClient.updateToken()
  }, [])

  useEffect(() => {
    void fetchVoiceEnums()
  }, [fetchVoiceEnums])

  useEffect(() => {
    if (ipKey) {
      void fetchVirtualIP()
    }
  }, [fetchVirtualIP, ipKey])

  useEffect(() => {
    if (voiceSettings.provider) {
      void fetchVoiceList(voiceTypeFilter, voiceSettings.provider)
    }
  }, [fetchVoiceList, voiceSettings.provider, voiceTypeFilter])

  useEffect(() => {
    setVoiceSettings((prev) => {
      if (prev.voice_type === voiceTypeFilter) return prev
      return { ...prev, voice_type: voiceTypeFilter, voice_id: undefined }
    })
  }, [voiceTypeFilter])

  useEffect(() => {
    if (!voiceList) return
    if (!voiceSettings.voice_id) {
      const first = voiceOptions[0]
      if (first) {
        setVoiceSettings((prev) => ({ ...prev, voice_id: prev.voice_id || first.value }))
      }
    }
  }, [voiceList, voiceTypeFilter, voiceSettings.voice_id, voiceOptions])

  useEffect(() => {
    if (voiceSettings.voice_type && voiceSettings.voice_type !== voiceTypeFilter) {
      setVoiceTypeFilter(voiceSettings.voice_type)
    }
  }, [voiceSettings.voice_type, voiceTypeFilter])

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
                href={`/virtual-ip/${virtualIP?.business_id || ipKey}/images`}
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
                  <Image src={virtualIP.default_avatar_url} alt={virtualIP.name} width={96} height={96} className="w-24 h-24 rounded-full object-cover" unoptimized />
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

          {/* 语音设置 */}
          <div className="p-8 border-b space-y-6">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">语音设置</h3>
                <p className="text-sm text-gray-500">
                  按 provider → model → voice 绑定角色语音，可随时试听
                </p>
              </div>
              {!voiceEnums && (
                <span className="text-sm text-gray-500">语音选项加载中...</span>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  提供商
                </label>
                <select
                  value={voiceSettings.provider || ''}
                  onChange={(e) => {
                    const value = e.target.value || undefined
                    const defaultModel =
                      voiceEnums?.defaults?.tts_model || voiceEnums?.tts_models?.[0]?.value
                    setVoiceSettings((prev) => ({
                      ...prev,
                      provider: value,
                      model: prev.model ?? defaultModel,
                      voice_id: undefined
                    }))
                  }}
                  disabled={!editing}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {(voiceEnums?.providers || []).map((p) => (
                    <option key={p.value} value={p.value}>
                      {p.label_zh || p.label_en}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  语音模型
                </label>
                <select
                  value={voiceSettings.model || ''}
                  onChange={(e) =>
                    setVoiceSettings((prev) => ({ ...prev, model: e.target.value || undefined }))
                  }
                  disabled={!editing}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {(voiceEnums?.tts_models || []).map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label_zh || m.label_en}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  音色类型
                </label>
                <select
                  value={voiceTypeFilter}
                  onChange={(e) => setVoiceTypeFilter(e.target.value)}
                  disabled={!editing}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {(voiceEnums?.voice_types || []).map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label_zh || item.label_en}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center justify-between">
                  音色
                  {voiceLoading && <span className="text-xs text-gray-500">加载中...</span>}
                </label>
                <select
                  value={voiceSettings.voice_id || ''}
                  onChange={(e) =>
                    setVoiceSettings((prev) => ({ ...prev, voice_id: e.target.value || undefined }))
                  }
                  disabled={!editing || voiceLoading}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">请选择音色</option>
                  {voiceOptions.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-xs text-gray-500">
                  来自 {voiceSettings.provider || '默认'} / {voiceSettings.model || '未选择'}
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">试听文本</label>
              <textarea
                value={voicePreviewText}
                onChange={(e) => setVoicePreviewText(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="输入要试听的文本"
              />
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => void handlePreviewVoice()}
                  disabled={previewLoading}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-60"
                >
                  {previewLoading ? '生成中...' : '试听'}
                </button>
                {previewAudioUrl && (
                  <audio controls src={previewAudioUrl} className="w-full max-w-md">
                    您的浏览器不支持音频播放。
                  </audio>
                )}
              </div>
              <p className="text-sm text-gray-500">
                保存后将把该音色绑定到当前角色，其他功能可直接复用。
              </p>
            </div>
          </div>

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
