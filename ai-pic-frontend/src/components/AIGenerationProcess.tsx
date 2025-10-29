'use client'

import React, { useCallback, useEffect, useState } from 'react'
import { virtualIPAPI, AIGenerationDetails } from '@/utils/api'

interface AIGenerationProcessProps {
  isOpen: boolean
  onClose: () => void
  name: string
  basicInfo?: string
  stylePreference?: string
  onComplete: (result: {
    description: string
    background_story: string
    biography: string
    style_prompt: string
    generation_details: AIGenerationDetails
  }) => void
}

type AIGenerationResult = {
  description: string
  background_story: string
  biography: string
  style_prompt: string
  generation_details: AIGenerationDetails
}

export default function AIGenerationProcess({
  isOpen,
  onClose,
  name,
  basicInfo,
  stylePreference,
  onComplete
}: AIGenerationProcessProps) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [currentStep, setCurrentStep] = useState('')
  const [steps, setSteps] = useState<string[]>([])
  const [generationDetails, setGenerationDetails] = useState<AIGenerationDetails | null>(null)
  const [result, setResult] = useState<AIGenerationResult | null>(null)
  const [showDetails, setShowDetails] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const startGeneration = useCallback(async () => {
    if (!name.trim()) {
      setError('请先输入虚拟IP名称')
      return
    }

    setIsGenerating(true)
    setError(null)
    setSteps([])
    setCurrentStep('开始AI生成...')
    
    try {
      const response = await virtualIPAPI.generateAIContentDetailed({
        name,
        basic_info: basicInfo || undefined,
        style_preference: stylePreference || undefined,
        image_category: 'portrait'
      })
      
      if (response.success && response.data) {
        setResult(response.data)
        setGenerationDetails(response.data.generation_details)
        setSteps(response.data.generation_details.steps)
        setCurrentStep('生成完成！')
      } else {
        setError('AI生成失败: ' + (response.error || '未知错误'))
      }
    } catch (error) {
      console.error('AI生成失败:', error)
      setError('AI生成失败，请检查网络连接或稍后重试')
    } finally {
      setIsGenerating(false)
    }
  }, [basicInfo, name, stylePreference])

  useEffect(() => {
    if (isOpen && name.trim()) {
      void startGeneration()
    }
  }, [isOpen, name, startGeneration])

  const handleComplete = () => {
    if (result) {
      onComplete(result)
      onClose()
    }
  }

  const handleClose = () => {
    setIsGenerating(false)
    setSteps([])
    setCurrentStep('')
    setResult(null)
    setGenerationDetails(null)
    setError(null)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
              <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-900">AI智能生成</h3>
              <p className="text-sm text-gray-500">正在为“{name}”生成完整内容</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            disabled={isGenerating}
            className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* 输入信息预览 */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h4 className="text-md font-medium text-gray-900 mb-3">输入信息</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="font-medium text-gray-700">角色名称：</span>
                <span className="text-gray-600">{name}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">基本信息：</span>
                <span className="text-gray-600">{basicInfo || '未提供'}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">风格偏好：</span>
                <span className="text-gray-600">{stylePreference || '现代风格'}</span>
              </div>
            </div>
          </div>

          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md">
              <div className="flex">
                <svg className="w-5 h-5 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {error}
              </div>
            </div>
          )}

          {/* 生成进度 */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-md font-medium text-gray-900">生成进度</h4>
              {isGenerating && (
                <div className="flex items-center text-sm text-blue-600">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  处理中...
                </div>
              )}
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="space-y-2">
                {steps.map((step, index) => (
                  <div key={index} className="flex items-center text-sm">
                    <div className="w-5 h-5 rounded-full bg-green-100 text-green-600 flex items-center justify-center mr-3">
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <span className="text-gray-700">{step}</span>
                  </div>
                ))}
                {currentStep && isGenerating && (
                  <div className="flex items-center text-sm">
                    <div className="w-5 h-5 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center mr-3">
                      <svg className="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    </div>
                    <span className="text-blue-600">{currentStep}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* AI生成详情 */}
          {generationDetails && (
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-md font-medium text-gray-900">生成详情</h4>
                <button
                  onClick={() => setShowDetails(!showDetails)}
                  className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                >
                  {showDetails ? '隐藏详情' : '查看详情'}
                </button>
              </div>

              <div className="bg-blue-50 rounded-lg p-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">AI模型：</span>
                    <br />
                    <span className="text-blue-600 font-mono">{generationDetails.model}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">温度参数：</span>
                    <br />
                    <span className="text-blue-600 font-mono">{generationDetails.temperature}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Token使用：</span>
                    <br />
                    <span className="text-blue-600 font-mono">{generationDetails.tokens_used}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">生成时间：</span>
                    <br />
                    <span className="text-blue-600 font-mono">{generationDetails.generation_time}s</span>
                  </div>
                </div>

                {showDetails && (
                  <div className="mt-4 pt-4 border-t border-blue-200">
                    <h5 className="font-medium text-gray-700 mb-3">使用的提示词：</h5>
                    <div className="space-y-3">
                      {generationDetails.prompts_used.map((prompt, index) => (
                        <div key={index} className="bg-white rounded p-3">
                          <div className="text-xs text-gray-500 mb-1">提示词 #{index + 1}</div>
                          <div className="text-sm font-mono text-gray-700 whitespace-pre-wrap">{prompt}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 生成结果预览 */}
          {result && (
            <div className="mb-6">
              <h4 className="text-md font-medium text-gray-900 mb-3">生成结果预览</h4>
              <div className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h5 className="font-medium text-green-800 mb-2">角色描述</h5>
                  <p className="text-green-700 text-sm">{result.description}</p>
                </div>
                
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h5 className="font-medium text-blue-800 mb-2">背景故事</h5>
                  <p className="text-blue-700 text-sm whitespace-pre-wrap">{result.background_story}</p>
                </div>
                
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <h5 className="font-medium text-purple-800 mb-2">人物小传</h5>
                  <p className="text-purple-700 text-sm whitespace-pre-wrap">{result.biography}</p>
                </div>

                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <h5 className="font-medium text-amber-800 mb-2">AI绘画提示词</h5>
                  <p className="text-amber-700 text-sm font-mono">{result.style_prompt}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end space-x-3 px-6 py-4 border-t">
          <button
            onClick={handleClose}
            disabled={isGenerating}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
          >
            {result ? '关闭' : '取消'}
          </button>
          
          {result && !isGenerating && (
            <button
              onClick={handleComplete}
              className="px-6 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-pink-500 rounded-md hover:from-purple-600 hover:to-pink-600 transition-all duration-200"
            >
              使用此结果创建IP
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
