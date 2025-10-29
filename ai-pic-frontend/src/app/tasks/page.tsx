'use client'

import { useState, useEffect, type FormEvent } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import { taskAPI, type Task as APITask } from '@/utils/api'
import { useAlertModal } from '@/components/AlertModalProvider'

interface GalleryImageItem {
  id: string
  title: string
  prompt: string
  platform: 'gpt' | 'keling' | 'jimeng'
  imageUrl: string
  createdAt: string
  tags: string[]
}

type TaskImage = File | GalleryImageItem

// 新建任务表单类型扩展
interface NewTaskForm {
  title: string
  prompt: string
  platform: string[]
  personImages?: TaskImage[]
  sceneImages?: TaskImage[]
  styleImages?: TaskImage[]
  count?: number
}

const isGalleryImage = (image: TaskImage): image is GalleryImageItem => {
  return typeof image === 'object' && image !== null && 'imageUrl' in image
}

const isFileImage = (image: TaskImage): image is File => image instanceof File

const extractUploadedFiles = (images?: TaskImage[]) => (images ?? []).filter(isFileImage)

const getTaskImageAlt = (image: TaskImage) => (isGalleryImage(image) ? image.title : image.name)

function TaskImagePreview({ image, alt, className }: { image: TaskImage; alt: string; className?: string }) {
  const [src, setSrc] = useState<string>()

  useEffect(() => {
    if (isGalleryImage(image)) {
      setSrc(image.imageUrl)
      return
    }

    const objectUrl = URL.createObjectURL(image)
    setSrc(objectUrl)

    return () => {
      URL.revokeObjectURL(objectUrl)
    }
  }, [image])

  if (!src) {
    return null
  }

  return (
    <Image
      src={src}
      alt={alt}
      width={64}
      height={64}
      className={className}
      unoptimized
    />
  )
}

// 模型配置
const modelConfig = {
  gpt: [
    { id: 'gpt-4', name: 'GPT-4', description: '最新版本，效果最佳' },
    { id: 'gpt-3.5', name: 'GPT-3.5', description: '快速生成，成本较低' },
    { id: 'dall-e-3', name: 'DALL-E 3', description: '专业图像生成' },
    { id: 'dall-e-2', name: 'DALL-E 2', description: '经典图像生成' }
  ],
  keling: [
    { id: 'keling-v1', name: '可灵 V1', description: '基础版本' },
    { id: 'keling-v2', name: '可灵 V2', description: '增强版本' },
    { id: 'keling-pro', name: '可灵 Pro', description: '专业版本' }
  ],
  jimeng: [
    { id: 'jimeng-basic', name: '即梦基础版', description: '入门级模型' },
    { id: 'jimeng-advanced', name: '即梦高级版', description: '高质量生成' },
    { id: 'jimeng-ultra', name: '即梦超清版', description: '超高分辨率' }
  ]
};

export default function Tasks() {
  const [tasks, setTasks] = useState<APITask[]>([])
  const [loading, setLoading] = useState(true)
  const [poll, setPoll] = useState(false)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [isStartingId, setIsStartingId] = useState<number | null>(null)
  const [deletingTaskId, setDeletingTaskId] = useState<number | null>(null)

  const loadTasks = async (options?: { silent?: boolean }) => {
    if (!options?.silent) {
      setLoading(true)
    }
    try {
      const res = await taskAPI.getTasks()
      if (res.success && res.data) {
        const tasksData = res.data.tasks ?? []
        const normalizedTasks = tasksData.reduce<APITask[]>((acc, task) => {
          const taskId = typeof task.id === 'number' ? task.id : Number(task.id)
          if (!Number.isInteger(taskId)) {
            console.warn('跳过无效任务ID', task.id)
            return acc
          }
          acc.push({ ...task, id: taskId })
          return acc
        }, [])
        setTasks(normalizedTasks)
        setFetchError(null)
      } else {
        setFetchError(res.error || '获取任务列表失败')
      }
    } catch (e) {
      setFetchError(e instanceof Error ? e.message : '获取任务列表失败')
    } finally {
      if (!options?.silent) {
        setLoading(false)
      }
    }
  }

  useEffect(() => {
    loadTasks()
  }, [])

  useEffect(() => {
    if (!poll) return
    const t = setInterval(() => loadTasks({ silent: true }), 5000)
    return () => clearInterval(t)
  }, [poll])

  // 新建任务表单状态
  const [newTask, setNewTask] = useState<NewTaskForm>({
    title: '',
    prompt: '',
    platform: [],
    personImages: [],
    sceneImages: [],
    styleImages: [],
    count: 1
  });
  // 各类图库图片选择
  const [selectedPersonImages, setSelectedPersonImages] = useState<GalleryImageItem[]>([]);
  const [selectedSceneImages, setSelectedSceneImages] = useState<GalleryImageItem[]>([]);
  const [selectedStyleImages, setSelectedStyleImages] = useState<GalleryImageItem[]>([]);
  // 画廊图片（模拟，实际可从后端获取）
  const [galleryImages] = useState<GalleryImageItem[]>([
    {
      id: '1',
      title: '山水风景画',
      prompt: '美丽的山水风景画，夕阳西下，山峰倒影在湖水中',
      platform: 'gpt',
      imageUrl: 'https://via.placeholder.com/400x400/4F46E5/FFFFFF?text=山水风景',
      createdAt: '2024-01-15 10:35',
      tags: ['风景', '山水', '夕阳']
    },
    {
      id: '2',
      title: '现代女性肖像',
      prompt: '现代风格的女性肖像画，优雅的气质，柔和的色调',
      platform: 'keling',
      imageUrl: 'https://via.placeholder.com/400x400/EC4899/FFFFFF?text=女性肖像',
      createdAt: '2024-01-15 11:05',
      tags: ['人物', '肖像', '现代']
    },
    {
      id: '3',
      title: '未来城市夜景',
      prompt: '未来城市夜景，霓虹灯闪烁，飞行汽车穿梭',
      platform: 'jimeng',
      imageUrl: 'https://via.placeholder.com/400x400/10B981/FFFFFF?text=未来城市',
      createdAt: '2024-01-15 11:20',
      tags: ['科幻', '城市', '夜景']
    },
    {
      id: '4',
      title: '抽象艺术',
      prompt: '抽象艺术风格，色彩斑斓，充满想象力的构图',
      platform: 'gpt',
      imageUrl: 'https://via.placeholder.com/400x400/F59E0B/FFFFFF?text=抽象艺术',
      createdAt: '2024-01-15 12:00',
      tags: ['抽象', '艺术', '色彩']
    },
    {
      id: '5',
      title: '古风建筑',
      prompt: '中国传统古建筑，飞檐翘角，红墙绿瓦',
      platform: 'keling',
      imageUrl: 'https://via.placeholder.com/400x400/EF4444/FFFFFF?text=古风建筑',
      createdAt: '2024-01-15 12:30',
      tags: ['古风', '建筑', '传统']
    },
    {
      id: '6',
      title: '海洋世界',
      prompt: '深海世界，珊瑚礁，热带鱼群，阳光透过水面',
      platform: 'jimeng',
      imageUrl: 'https://via.placeholder.com/400x400/06B6D4/FFFFFF?text=海洋世界',
      createdAt: '2024-01-15 13:00',
      tags: ['海洋', '自然', '生物']
    }
  ]);

  const { showAlert } = useAlertModal()

  const handleCreateTask = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!newTask.platform.length) {
      showAlert({ message: '请至少选择一个模型', variant: 'warning' })
      return
    }
    setIsCreating(true)
    try {
      for (const modelId of newTask.platform) {
        const [platform] = modelId.split('-')
        const response = await taskAPI.createTask({
          title: newTask.title,
          prompt: newTask.prompt,
          platform: platform as 'gpt' | 'keling' | 'jimeng',
        })
        if (!response.success) {
          throw new Error(response.error || '创建任务失败')
        }
      }
      await loadTasks({ silent: true })
      setNewTask({
        title: '',
        prompt: '',
        platform: [],
        personImages: [],
        sceneImages: [],
        styleImages: [],
        count: 1,
      })
      setSelectedPersonImages([])
      setSelectedSceneImages([])
      setSelectedStyleImages([])
      setSelectedStyles([])
      setCustomStyleInput('')
      showAlert({ message: '任务已创建', variant: 'success' })
    } catch (error) {
      const message = error instanceof Error ? error.message : '创建任务失败'
      console.error('创建任务失败:', error)
      showAlert({ message, variant: 'error' })
    } finally {
      setIsCreating(false)
    }
  }

  const getStatusColor = (status: APITask['status']) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800'
      case 'processing': return 'bg-blue-100 text-blue-800'
      case 'completed': return 'bg-green-100 text-green-800'
      case 'failed': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusText = (status: APITask['status']) => {
    switch (status) {
      case 'pending': return '等待中'
      case 'processing': return '生成中'
      case 'completed': return '已完成'
      case 'failed': return '失败'
      default: return '未知'
    }
  }

  const handleStart = async (id: APITask['id']) => {
    const taskId = typeof id === 'number' ? id : Number(id)
    if (!Number.isInteger(taskId)) {
      showAlert({ message: '任务编号无效，无法启动任务', variant: 'warning' })
      return
    }
    setIsStartingId(taskId)
    try {
      const res = await taskAPI.startTask(taskId)
      if (res.success) {
        await loadTasks({ silent: true })
        showAlert({ message: res.data?.message || '任务已开始执行', variant: 'success' })
      } else {
        throw new Error(res.error || '启动任务失败')
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : '启动任务失败'
      console.error('启动任务失败:', error)
      showAlert({ message, variant: 'error' })
    } finally {
      setIsStartingId(null)
    }
  }

  const deleteTaskCore = async (taskId: number) => {
    setDeletingTaskId(taskId)
    try {
      const res = await taskAPI.deleteTask(String(taskId))
      if (res.success) {
        setTasks(prev => prev.filter(t => t.id !== taskId))
        await loadTasks({ silent: true })
      } else {
        throw new Error(res.error || '删除任务失败')
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : '删除任务失败'
      console.error('删除任务失败:', error)
      showAlert({ message, variant: 'error' })
    } finally {
      setDeletingTaskId(null)
    }
  }

  const handleDelete = (id: APITask['id']) => {
    const taskId = typeof id === 'number' ? id : Number(id)
    if (!Number.isInteger(taskId)) {
      showAlert({ message: '任务编号无效，无法删除', variant: 'warning' })
      return
    }
    showAlert({
      title: '确认删除任务',
      message: '确定删除该任务吗？',
      variant: 'warning',
      confirmText: '删除',
      onConfirm: () => {
        void deleteTaskCore(taskId)
      },
    })
  }

  const styleOptions = ['油画', '水彩', '赛博朋克', '写实', '二次元', '国风', '未来感'];
  const [selectedStyles, setSelectedStyles] = useState<string[]>([]);
  const [customStyleInput, setCustomStyleInput] = useState('');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-8">
              <h1 className="text-2xl font-bold text-gray-900">任务管理</h1>
              <nav className="flex space-x-8">
                <Link href="/tasks" className="text-blue-600 border-b-2 border-blue-600 px-3 py-2 text-sm font-medium">
                  任务管理
                </Link>
                <Link href="/gallery" className="text-gray-500 hover:text-gray-900 px-3 py-2 text-sm font-medium">
                  图片画廊
                </Link>
              </nav>
            </div>
            <div className="flex items-center space-x-4">
              <label className="text-sm text-gray-600 flex items-center gap-2">
                <input type="checkbox" checked={poll} onChange={e => setPoll(e.target.checked)} /> 自动刷新
              </label>
              <button onClick={() => loadTasks()} className="text-sm text-blue-600 hover:text-blue-800">刷新</button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row gap-8 items-start">
          {/* 左侧：生成配置表单 */}
          <div className="w-full md:w-1/2 bg-white shadow rounded-lg p-6 sticky top-8">
            <h3 className="text-lg font-medium text-gray-900 mb-4">生成配置</h3>
            <form onSubmit={handleCreateTask} className="space-y-6">
              <div className="space-y-4">
                {/* 标题 */}
                <label className="block text-sm font-medium text-gray-700 mb-1">任务标题</label>
                <input type="text" value={newTask.title} onChange={(e) => setNewTask({...newTask, title: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500" placeholder="请输入任务标题" required />
                {/* 提示词 */}
                <label className="block text-sm font-medium text-gray-700 mb-1">提示词</label>
                <textarea value={newTask.prompt} onChange={(e) => setNewTask({...newTask, prompt: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500" rows={4} placeholder="请详细描述你想要生成的图片内容" required />
                {/* 平台多选 */}
                <label className="block text-sm font-medium text-gray-700 mb-1">AI模型（可多选）</label>
                <div className="space-y-3">
                  {Object.entries(modelConfig).map(([platform, models]) => (
                    <div key={platform} className="border border-gray-200 rounded-lg p-3">
                      <h4 className="font-medium text-gray-900 mb-2 text-sm">
                        {platform === 'gpt' ? 'GPT' : platform === 'keling' ? '可灵' : '即梦'}
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {models.map(model => (
                          <button
                            key={model.id}
                            type="button"
                            onClick={() => {
                              if (newTask.platform.includes(model.id)) {
                                setNewTask({ ...newTask, platform: newTask.platform.filter(p => p !== model.id) });
                              } else {
                                setNewTask({ ...newTask, platform: [...newTask.platform, model.id] });
                              }
                            }}
                            className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                              newTask.platform.includes(model.id)
                                ? 'bg-blue-500 text-white border-blue-500'
                                : 'bg-white text-gray-700 border-gray-300 hover:border-blue-300'
                            }`}
                            title={model.description}
                          >
                            {model.name}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                {/* 已选模型标签 */}
                {newTask.platform.length > 0 && (
                  <div className="mt-3">
                    <label className="block text-sm font-medium text-gray-700 mb-2">已选模型</label>
                    <div className="flex flex-wrap gap-2">
                      {newTask.platform.map(modelId => {
                        const [platform] = modelId.split('-');
                        const model = modelConfig[platform as keyof typeof modelConfig]?.find(m => m.id === modelId);
                        return (
                          <span key={modelId} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs flex items-center">
                            {model?.name || modelId}
                            <button
                              type="button"
                              className="ml-1 text-blue-500 hover:text-blue-700"
                              onClick={() => setNewTask({ ...newTask, platform: newTask.platform.filter(p => p !== modelId) })}
                            >
                              ×
                            </button>
                          </span>
                        );
                      })}
                    </div>
                  </div>
                )}
                {/* 生成数量 */}
                <label className="block text-sm font-medium text-gray-700 mb-1">生成数量</label>
                <input
                  type="number"
                  min={1}
                  max={10}
                  value={newTask.count}
                  onChange={e => setNewTask({ ...newTask, count: Math.max(1, Math.min(10, Number(e.target.value))) })}
                  className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="1-10"
                  required
                />
                {/* 风格 */}
                <label className="block text-sm font-medium text-gray-700 mb-1">风格（可多选或自定义）</label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {styleOptions.map(opt => (
                    <button
                      type="button"
                      key={opt}
                      className={`px-3 py-1 rounded border ${selectedStyles.includes(opt) ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-gray-700 border-gray-300'}`}
                      onClick={() => {
                        setSelectedStyles(selectedStyles.includes(opt)
                          ? selectedStyles.filter(s => s !== opt)
                          : [...selectedStyles, opt]);
                      }}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="自定义风格，多个用逗号分隔"
                  value={customStyleInput}
                  onChange={e => setCustomStyleInput(e.target.value)}
                  onBlur={() => {
                    if (customStyleInput.trim()) {
                      const customs = customStyleInput.split(',').map(s => s.trim()).filter(Boolean);
                      setSelectedStyles([...new Set([...selectedStyles, ...customs])]);
                      setCustomStyleInput('');
                    }
                  }}
                  onKeyDown={e => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      if (customStyleInput.trim()) {
                        const customs = customStyleInput.split(',').map(s => s.trim()).filter(Boolean);
                        setSelectedStyles([...new Set([...selectedStyles, ...customs])]);
                        setCustomStyleInput('');
                      }
                    }
                  }}
                />
                <div className="mt-1 text-xs text-gray-400">如：油画、水彩、赛博朋克、写实、二次元、国风、未来感等</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {selectedStyles.map(style => (
                    <span key={style} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs flex items-center">
                      {style}
                      <button type="button" className="ml-1 text-blue-500 hover:text-blue-700" onClick={() => setSelectedStyles(selectedStyles.filter(s => s !== style))}>×</button>
                    </span>
                  ))}
                </div>
                {/* 参考图片-人物 */}
                <label className="block text-sm font-medium text-gray-700 mb-1">人物参考图片（可多选）</label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-blue-400 transition-colors">
                  <input 
                    type="file" 
                    accept="image/*" 
                    multiple 
                    onChange={e => {
                      const files = e.target.files;
                      if (!files) return;
                      setNewTask({
                        ...newTask,
                        personImages: [...(newTask.personImages ?? []), ...Array.from(files)],
                      });
                    }}
                    className="hidden"
                    id="person-upload"
                  />
                  <label htmlFor="person-upload" className="cursor-pointer">
                    <svg className="mx-auto h-8 w-8 text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <p className="text-sm text-gray-600">点击上传或拖拽图片到此处</p>
                    <p className="text-xs text-gray-400 mt-1">支持 JPG、PNG、GIF 格式</p>
                  </label>
                </div>
                <div className="flex flex-wrap gap-2 mt-2">
                  {galleryImages.filter(img => img.tags.includes('人物')).map(img => (
                    <div
                      key={img.id}
                      className={`border rounded p-1 cursor-pointer ${selectedPersonImages.some(i => i.id === img.id) ? 'border-blue-500' : 'border-gray-300'}`}
                      onClick={() => {
                        const isSelected = selectedPersonImages.some(i => i.id === img.id)
                        const nextSelected = isSelected
                          ? selectedPersonImages.filter(i => i.id !== img.id)
                          : [...selectedPersonImages, img]
                        setSelectedPersonImages(nextSelected)
                        const uploadedFiles = extractUploadedFiles(newTask.personImages)
                        setNewTask({
                          ...newTask,
                          personImages: [...uploadedFiles, ...nextSelected],
                        })
                      }}
                    >
                      <Image
                        src={img.imageUrl}
                        alt={img.title}
                        width={64}
                        height={64}
                        className="w-16 h-16 object-cover rounded"
                        unoptimized
                      />
                    </div>
                  ))}
                </div>
                {/* 已选人物图片 */}
                {newTask.personImages && newTask.personImages.length > 0 && (
                  <div className="mt-2">
                    <div className="text-xs text-gray-500 mb-1">已选人物图片：</div>
                    <div className="flex flex-wrap gap-2">
                      {newTask.personImages.map((img, index) => (
                        <div key={index} className="relative group">
                          <TaskImagePreview
                            image={img}
                            alt={getTaskImageAlt(img)}
                            className="w-16 h-16 object-cover rounded border"
                          />
                          <button
                            type="button"
                            onClick={() => {
                              if (!newTask.personImages) return
                              const nextImages = [...newTask.personImages]
                              const [removed] = nextImages.splice(index, 1)
                              setNewTask({ ...newTask, personImages: nextImages })
                              if (removed && isGalleryImage(removed)) {
                                setSelectedPersonImages(prev => prev.filter(i => i.id !== removed.id))
                              }
                            }}
                            className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {/* 参考图片-场景 */}
                <label className="block text-sm font-medium text-gray-700 mb-1 mt-4">场景参考图片（可多选）</label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-blue-400 transition-colors">
                  <input 
                    type="file" 
                    accept="image/*" 
                    multiple 
                    onChange={e => {
                      const files = e.target.files;
                      if (!files) return;
                      setNewTask({
                        ...newTask,
                        sceneImages: [...(newTask.sceneImages ?? []), ...Array.from(files)],
                      });
                    }}
                    className="hidden"
                    id="scene-upload"
                  />
                  <label htmlFor="scene-upload" className="cursor-pointer">
                    <svg className="mx-auto h-8 w-8 text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <p className="text-sm text-gray-600">点击上传或拖拽图片到此处</p>
                    <p className="text-xs text-gray-400 mt-1">支持 JPG、PNG、GIF 格式</p>
                  </label>
                </div>
                <div className="flex flex-wrap gap-2 mt-2">
                  {galleryImages.filter(img => img.tags.some(t => ['风景','场景','城市','建筑','自然','夜景'].includes(t))).map(img => (
                    <div
                      key={img.id}
                      className={`border rounded p-1 cursor-pointer ${selectedSceneImages.some(i => i.id === img.id) ? 'border-blue-500' : 'border-gray-300'}`}
                      onClick={() => {
                        const isSelected = selectedSceneImages.some(i => i.id === img.id)
                        const nextSelected = isSelected
                          ? selectedSceneImages.filter(i => i.id !== img.id)
                          : [...selectedSceneImages, img]
                        setSelectedSceneImages(nextSelected)
                        const uploadedFiles = extractUploadedFiles(newTask.sceneImages)
                        setNewTask({
                          ...newTask,
                          sceneImages: [...uploadedFiles, ...nextSelected],
                        })
                      }}
                    >
                      <Image
                        src={img.imageUrl}
                        alt={img.title}
                        width={64}
                        height={64}
                        className="w-16 h-16 object-cover rounded"
                        unoptimized
                      />
                    </div>
                  ))}
                </div>
                {/* 已选场景图片 */}
                {newTask.sceneImages && newTask.sceneImages.length > 0 && (
                  <div className="mt-2">
                    <div className="text-xs text-gray-500 mb-1">已选场景图片：</div>
                    <div className="flex flex-wrap gap-2">
                      {newTask.sceneImages.map((img, index) => (
                        <div key={index} className="relative group">
                          <TaskImagePreview
                            image={img}
                            alt={getTaskImageAlt(img)}
                            className="w-16 h-16 object-cover rounded border"
                          />
                          <button
                            type="button"
                            onClick={() => {
                              if (!newTask.sceneImages) return
                              const nextImages = [...newTask.sceneImages]
                              const [removed] = nextImages.splice(index, 1)
                              setNewTask({ ...newTask, sceneImages: nextImages })
                              if (removed && isGalleryImage(removed)) {
                                setSelectedSceneImages(prev => prev.filter(i => i.id !== removed.id))
                              }
                            }}
                            className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {/* 参考图片-风格 */}
                <label className="block text-sm font-medium text-gray-700 mb-1 mt-4">风格参考图片（可多选）</label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-blue-400 transition-colors">
                  <input 
                    type="file" 
                    accept="image/*" 
                    multiple 
                    onChange={e => {
                      const files = e.target.files;
                      if (!files) return;
                      setNewTask({
                        ...newTask,
                        styleImages: [...(newTask.styleImages ?? []), ...Array.from(files)],
                      });
                    }}
                    className="hidden"
                    id="style-upload"
                  />
                  <label htmlFor="style-upload" className="cursor-pointer">
                    <svg className="mx-auto h-8 w-8 text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <p className="text-sm text-gray-600">点击上传或拖拽图片到此处</p>
                    <p className="text-xs text-gray-400 mt-1">支持 JPG、PNG、GIF 格式</p>
                  </label>
                </div>
                <div className="flex flex-wrap gap-2 mt-2">
                  {galleryImages.filter(img => img.tags.some(t => ['风格','抽象','艺术','色彩','国风','现代','赛博朋克','写实','二次元','未来感'].includes(t))).map(img => (
                    <div
                      key={img.id}
                      className={`border rounded p-1 cursor-pointer ${selectedStyleImages.some(i => i.id === img.id) ? 'border-blue-500' : 'border-gray-300'}`}
                      onClick={() => {
                        const isSelected = selectedStyleImages.some(i => i.id === img.id)
                        const nextSelected = isSelected
                          ? selectedStyleImages.filter(i => i.id !== img.id)
                          : [...selectedStyleImages, img]
                        setSelectedStyleImages(nextSelected)
                        const uploadedFiles = extractUploadedFiles(newTask.styleImages)
                        setNewTask({
                          ...newTask,
                          styleImages: [...uploadedFiles, ...nextSelected],
                        })
                      }}
                    >
                      <Image
                        src={img.imageUrl}
                        alt={img.title}
                        width={64}
                        height={64}
                        className="w-16 h-16 object-cover rounded"
                        unoptimized
                      />
                    </div>
                  ))}
                </div>
                {/* 已选风格图片 */}
                {newTask.styleImages && newTask.styleImages.length > 0 && (
                  <div className="mt-2">
                    <div className="text-xs text-gray-500 mb-1">已选风格图片：</div>
                    <div className="flex flex-wrap gap-2">
                      {newTask.styleImages.map((img, index) => (
                        <div key={index} className="relative group">
                          <TaskImagePreview
                            image={img}
                            alt={getTaskImageAlt(img)}
                            className="w-16 h-16 object-cover rounded border"
                          />
                          <button
                            type="button"
                            onClick={() => {
                              if (!newTask.styleImages) return
                              const nextImages = [...newTask.styleImages]
                              const [removed] = nextImages.splice(index, 1)
                              setNewTask({ ...newTask, styleImages: nextImages })
                              if (removed && isGalleryImage(removed)) {
                                setSelectedStyleImages(prev => prev.filter(i => i.id !== removed.id))
                              }
                            }}
                            className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <hr className="my-4" />
              <div className="flex space-x-3 justify-end">
                <button
                  type="submit"
                  disabled={isCreating}
                  className="bg-blue-600 text-white py-2 px-6 rounded-md hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isCreating ? '创建中...' : '创建任务'}
                </button>
              </div>
            </form>
          </div>
          {/* 右侧：任务列表 */}
          <div className="w-full md:w-1/2 bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">任务列表</h2>
              {fetchError && (
                <p className="mt-2 text-sm text-red-600">{fetchError}</p>
              )}
              {loading && (
                <p className="mt-2 text-sm text-gray-500">加载中...</p>
              )}
            </div>
            <div className="divide-y divide-gray-200">
              {!loading && !fetchError && tasks.length === 0 && (
                <div className="p-6 text-sm text-gray-500">暂无任务，先创建一个吧。</div>
              )}
              {tasks.map((task) => (
                <div key={task.id} className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-lg font-medium text-gray-900">{task.title}</h3>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(task.status)}`}>
                          {getStatusText(task.status)}
                        </span>
                        {/* 平台标签移除：后端任务未提供平台字段 */}
                      </div>
                      {task.prompt && <p className="text-gray-600 mb-3">{task.prompt}</p>}
                      <div className="flex items-center space-x-6 text-sm text-gray-500">
                        <span>创建时间：{task.created_at ? new Date(task.created_at).toLocaleString() : '未知'}</span>
                        {task.updated_at && <span>更新时间：{new Date(task.updated_at).toLocaleString()}</span>}
                        {task.description && <span>描述：{task.description}</span>}
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      {task.status === 'processing' && (
                        <div className="flex items-center space-x-2">
                          <svg className="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          <span className="text-blue-600">生成中...</span>
                        </div>
                      )}
                      {task.status === 'pending' && (
                        <button
                          onClick={() => handleStart(task.id)}
                          disabled={isStartingId === task.id}
                          className="text-blue-600 hover:text-blue-800 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {isStartingId === task.id ? '启动中...' : '开始'}
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(task.id)}
                        disabled={deletingTaskId === task.id}
                        className="text-red-600 hover:text-red-800 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {deletingTaskId === task.id ? '删除中...' : '删除'}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
} 
