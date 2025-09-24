'use client'

import Link from 'next/link'
import Navigation from '@/components/Navigation'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Navigation />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            以虚拟IP为中心的AI短剧制作平台
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            集成多种AI能力，支持虚拟IP管理、AI图像生成、剧本创作等完整短剧制作工作流
          </p>
          <div className="flex justify-center space-x-4">
            <Link href="/virtual-ip" className="bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-medium hover:bg-blue-700 transition-colors">
              虚拟IP管理
            </Link>
            <Link href="/stories" className="bg-green-600 text-white px-8 py-3 rounded-lg text-lg font-medium hover:bg-green-700 transition-colors">
              剧本创作
            </Link>
            <Link href="/gallery" className="bg-purple-600 text-white px-8 py-3 rounded-lg text-lg font-medium hover:bg-purple-700 transition-colors">
              作品展示
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-4 gap-8 mb-16">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <span className="text-2xl">🎭</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">虚拟IP管理</h3>
            <p className="text-gray-600">创建和管理虚拟角色，AI生成角色图像，构建完整的IP档案</p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <span className="text-2xl">🤖</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">AI剧本生成</h3>
            <p className="text-gray-600">基于虚拟IP生成故事概要、剧集大纲、完整剧本</p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <span className="text-2xl">🎨</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">AI图像生成</h3>
            <p className="text-gray-600">支持多种AI服务，生成高质量的角色图像和场景图</p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4">
              <span className="text-2xl">⚡</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">工作流自动化</h3>
            <p className="text-gray-600">完整的制作流程，从故事创意到最终剧本的自动化生成</p>
          </div>
        </div>

        {/* Workflow Section */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-16">
          <h3 className="text-2xl font-bold text-gray-900 mb-8 text-center">制作工作流</h3>
          <div className="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0 md:space-x-4">
            <div className="flex-1 text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">👥</span>
              </div>
              <h4 className="font-semibold text-gray-900 mb-2">1. 创建虚拟IP</h4>
              <p className="text-gray-600 text-sm">定义角色属性，AI生成角色图像</p>
            </div>
            
            <div className="hidden md:block">
              <span className="text-gray-400">→</span>
            </div>
            
            <div className="flex-1 text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">📚</span>
              </div>
              <h4 className="font-semibold text-gray-900 mb-2">2. 生成故事概要</h4>
              <p className="text-gray-600 text-sm">基于角色组合，AI生成故事大纲</p>
            </div>
            
            <div className="hidden md:block">
              <span className="text-gray-400">→</span>
            </div>
            
            <div className="flex-1 text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🎬</span>
              </div>
              <h4 className="font-semibold text-gray-900 mb-2">3. 生成剧集大纲</h4>
              <p className="text-gray-600 text-sm">将故事拆分为多个剧集</p>
            </div>
            
            <div className="hidden md:block">
              <span className="text-gray-400">→</span>
            </div>
            
            <div className="flex-1 text-center">
              <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">📝</span>
              </div>
              <h4 className="font-semibold text-gray-900 mb-2">4. 生成完整剧本</h4>
              <p className="text-gray-600 text-sm">基于剧集大纲生成详细剧本</p>
            </div>
          </div>
        </div>

        {/* Quick Start Section */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-8 text-center">
          <h3 className="text-2xl font-bold text-white mb-4">开始您的AI短剧创作之旅</h3>
          <p className="text-blue-100 mb-6">只需几步，即可创建专业的短剧剧本</p>
          <div className="flex justify-center space-x-4">
            <Link href="/virtual-ip" className="bg-white text-blue-600 px-6 py-3 rounded-lg font-medium hover:bg-gray-100 transition-colors">
              创建虚拟IP
            </Link>
            <Link href="/stories" className="bg-blue-500 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-400 transition-colors">
              开始创作
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-8 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p>&copy; 2024 AI短剧制作工作流平台. 保留所有权利.</p>
        </div>
      </footer>
    </div>
  )
}
