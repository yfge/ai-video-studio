'use client'

import { useState } from 'react'
import Link from 'next/link'

interface ImageItem {
  id: string
  title: string
  prompt: string
  platform: 'gpt' | 'keling' | 'jimeng'
  imageUrl: string
  createdAt: string
  tags: string[]
}

export default function Gallery() {
  const [images, setImages] = useState<ImageItem[]>([
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
  ])

  const [searchTerm, setSearchTerm] = useState('')
  const [selectedPlatform, setSelectedPlatform] = useState<string>('all')
  const [selectedImage, setSelectedImage] = useState<ImageItem | null>(null)

  const filteredImages = images.filter(image => {
    const matchesSearch = image.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         image.prompt.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         image.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
    
    const matchesPlatform = selectedPlatform === 'all' || image.platform === selectedPlatform
    
    return matchesSearch && matchesPlatform
  })

  const getPlatformText = (platform: ImageItem['platform']) => {
    switch (platform) {
      case 'gpt': return 'GPT'
      case 'keling': return '可灵'
      case 'jimeng': return '即梦'
      default: return '未知'
    }
  }

  const handleDownload = (image: ImageItem) => {
    // 模拟下载功能
    const link = document.createElement('a')
    link.href = image.imageUrl
    link.download = `${image.title}.jpg`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-8">
              <h1 className="text-2xl font-bold text-gray-900">图片画廊</h1>
              <nav className="flex space-x-8">
                <Link href="/tasks" className="text-gray-500 hover:text-gray-900 px-3 py-2 text-sm font-medium">
                  任务管理
                </Link>
                <Link href="/gallery" className="text-blue-600 border-b-2 border-blue-600 px-3 py-2 text-sm font-medium">
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
        {/* Filters */}
        <div className="bg-white p-6 rounded-lg shadow mb-8">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
                搜索
              </label>
              <input
                type="text"
                id="search"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="搜索图片标题、描述或标签..."
              />
            </div>
            
            <div className="sm:w-48">
              <label htmlFor="platform" className="block text-sm font-medium text-gray-700 mb-1">
                AI平台
              </label>
              <select
                id="platform"
                value={selectedPlatform}
                onChange={(e) => setSelectedPlatform(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">全部平台</option>
                <option value="gpt">GPT</option>
                <option value="keling">可灵</option>
                <option value="jimeng">即梦</option>
              </select>
            </div>
          </div>
        </div>

        {/* Image Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredImages.map((image) => (
            <div key={image.id} className="bg-white rounded-lg shadow overflow-hidden hover:shadow-lg transition-shadow">
              <div className="relative group">
                <img
                  src={image.imageUrl}
                  alt={image.title}
                  className="w-full h-64 object-cover cursor-pointer"
                  onClick={() => setSelectedImage(image)}
                />
                
                {/* Overlay */}
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all duration-200 flex items-center justify-center">
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex space-x-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedImage(image)
                      }}
                      className="bg-white text-gray-800 px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100"
                    >
                      查看
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDownload(image)
                      }}
                      className="bg-blue-600 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700"
                    >
                      下载
                    </button>
                  </div>
                </div>
              </div>
              
              <div className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-medium text-gray-900 truncate">{image.title}</h3>
                  <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">
                    {getPlatformText(image.platform)}
                  </span>
                </div>
                
                <p className="text-gray-600 text-sm mb-3 line-clamp-2">{image.prompt}</p>
                
                <div className="flex flex-wrap gap-1 mb-3">
                  {image.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
                
                <p className="text-xs text-gray-500">{image.createdAt}</p>
              </div>
            </div>
          ))}
        </div>

        {filteredImages.length === 0 && (
          <div className="text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">没有找到图片</h3>
            <p className="mt-1 text-sm text-gray-500">尝试调整搜索条件或创建新任务</p>
          </div>
        )}
      </main>

      {/* Image Modal */}
      {selectedImage && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-medium text-gray-900">{selectedImage.title}</h3>
                <button
                  onClick={() => setSelectedImage(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <img
                src={selectedImage.imageUrl}
                alt={selectedImage.title}
                className="w-full h-96 object-cover rounded-lg mb-4"
              />
              
              <div className="space-y-3">
                <div>
                  <h4 className="text-sm font-medium text-gray-700">描述</h4>
                  <p className="text-sm text-gray-600">{selectedImage.prompt}</p>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">
                      {getPlatformText(selectedImage.platform)}
                    </span>
                    <span className="text-sm text-gray-500">{selectedImage.createdAt}</span>
                  </div>
                  
                  <button
                    onClick={() => handleDownload(selectedImage)}
                    className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700"
                  >
                    下载图片
                  </button>
                </div>
                
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">标签</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedImage.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
} 