'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import AdminLayout from '../../../components/AdminLayout'
import { adminAPI, UserStatsResponse } from '../../../utils/api'

// 简单的图标组件
const UsersIcon = ({ className = '' }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-2.239" />
  </svg>
)

const CheckCircleIcon = ({ className = '' }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
)

const ClockIcon = ({ className = '' }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
)

const XCircleIcon = ({ className = '' }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
)

const ShieldCheckIcon = ({ className = '' }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
  </svg>
)

const TrendingUpIcon = ({ className = '' }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
  </svg>
)

interface StatCard {
  title: string
  value: number
  icon: React.ComponentType<{ className?: string }>
  color: string
  bgColor: string
  textColor: string
  href?: string
  description?: string
}

export default function AdminStatsPage() {
  const [stats, setStats] = useState<UserStatsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 加载统计数据
  const loadStats = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await adminAPI.getUserStats()
      
      if (response.success && response.data) {
        setStats(response.data)
      } else {
        setError(response.error || '获取统计数据失败')
      }
    } catch (err) {
      setError('网络错误，请稍后重试')
      console.error('加载统计数据失败:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadStats()
  }, [])

  // 统计卡片配置
  const getStatCards = (stats: UserStatsResponse): StatCard[] => [
    {
      title: '总用户数',
      value: stats.total_users,
      icon: UsersIcon,
      color: 'blue',
      bgColor: 'bg-blue-50',
      textColor: 'text-blue-600',
      description: '系统中的所有用户'
    },
    {
      title: '活跃用户',
      value: stats.active_users,
      icon: CheckCircleIcon,
      color: 'green',
      bgColor: 'bg-green-50',
      textColor: 'text-green-600',
      href: '/admin/users?status=approved',
      description: '已激活且正常使用的用户'
    },
    {
      title: '待审批用户',
      value: stats.pending_approval,
      icon: ClockIcon,
      color: 'yellow',
      bgColor: 'bg-yellow-50',
      textColor: 'text-yellow-600',
      href: '/admin/users?status=pending',
      description: '等待管理员审批的新注册用户'
    },
    {
      title: '暂停用户',
      value: stats.suspended_users,
      icon: XCircleIcon,
      color: 'red',
      bgColor: 'bg-red-50',
      textColor: 'text-red-600',
      href: '/admin/users?status=suspended',
      description: '已被暂停使用的用户'
    },
    {
      title: '管理员用户',
      value: stats.admin_users,
      icon: ShieldCheckIcon,
      color: 'purple',
      bgColor: 'bg-purple-50',
      textColor: 'text-purple-600',
      href: '/admin/users?role=admin',
      description: '拥有管理权限的用户'
    },
    {
      title: '最近注册',
      value: stats.recent_registrations,
      icon: TrendingUpIcon,
      color: 'indigo',
      bgColor: 'bg-indigo-50',
      textColor: 'text-indigo-600',
      description: '最近7天的新注册用户'
    }
  ]

  if (loading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </AdminLayout>
    )
  }

  if (error) {
    return (
      <AdminLayout>
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <XCircleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">{error}</h3>
              <div className="mt-2">
                <button
                  onClick={loadStats}
                  className="text-sm text-red-600 hover:text-red-500 underline"
                >
                  重试
                </button>
              </div>
            </div>
          </div>
        </div>
      </AdminLayout>
    )
  }

  if (!stats) {
    return (
      <AdminLayout>
        <div className="text-center py-12">
          <p className="text-gray-500">暂无数据</p>
        </div>
      </AdminLayout>
    )
  }

  const statCards = getStatCards(stats)

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* 页面头部 */}
        <div className="sm:flex sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">统计数据</h1>
            <p className="mt-2 text-sm text-gray-700">
              用户管理系统的整体数据概览
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            <button
              onClick={loadStats}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              刷新数据
            </button>
          </div>
        </div>

        {/* 统计卡片网格 */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {statCards.map((card) => {
            const CardIcon = card.icon
            const cardContent = (
              <div className={`${card.bgColor} overflow-hidden shadow rounded-lg`}>
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <CardIcon className={`h-6 w-6 ${card.textColor}`} />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          {card.title}
                        </dt>
                        <dd>
                          <div className={`text-lg font-medium ${card.textColor}`}>
                            {card.value.toLocaleString()}
                          </div>
                        </dd>
                      </dl>
                    </div>
                  </div>
                  {card.description && (
                    <div className="mt-3">
                      <p className="text-xs text-gray-500">{card.description}</p>
                    </div>
                  )}
                </div>
                {card.href && (
                  <div className={`bg-gray-50 px-5 py-3`}>
                    <div className="text-sm">
                      <span className={`font-medium ${card.textColor} hover:opacity-80`}>
                        查看详情 →
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )

            return card.href ? (
              <Link key={card.title} href={card.href} className="block hover:opacity-95">
                {cardContent}
              </Link>
            ) : (
              <div key={card.title}>{cardContent}</div>
            )
          })}
        </div>

        {/* 快速操作区域 */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              快速操作
            </h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Link
                href="/admin/users?status=pending"
                className="relative group bg-white p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-blue-500 rounded-lg border border-gray-200 hover:border-gray-300"
              >
                <div>
                  <span className="rounded-lg inline-flex p-3 bg-yellow-50 text-yellow-600 ring-4 ring-white">
                    <ClockIcon className="h-6 w-6" />
                  </span>
                </div>
                <div className="mt-4">
                  <h3 className="text-lg font-medium text-gray-900">
                    处理待审批
                    {stats.pending_approval > 0 && (
                      <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        {stats.pending_approval}
                      </span>
                    )}
                  </h3>
                  <p className="mt-2 text-sm text-gray-500">
                    查看和处理等待审批的用户申请
                  </p>
                </div>
                <span className="pointer-events-none absolute top-6 right-6 text-gray-300 group-hover:text-gray-400">
                  <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20 4h1a1 1 0 00-1-1v1zm-1 12a1 1 0 102 0h-2zM8 3a1 1 0 000 2V3zM3.293 19.293a1 1 0 101.414 1.414l-1.414-1.414zM19 4v12h2V4h-2zm1-1H8v2h12V3zm-.707.293l-16 16 1.414 1.414 16-16L19.293 3.293z"/>
                  </svg>
                </span>
              </Link>

              <Link
                href="/admin/users"
                className="relative group bg-white p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-blue-500 rounded-lg border border-gray-200 hover:border-gray-300"
              >
                <div>
                  <span className="rounded-lg inline-flex p-3 bg-blue-50 text-blue-600 ring-4 ring-white">
                    <UsersIcon className="h-6 w-6" />
                  </span>
                </div>
                <div className="mt-4">
                  <h3 className="text-lg font-medium text-gray-900">
                    管理用户
                  </h3>
                  <p className="mt-2 text-sm text-gray-500">
                    查看和管理所有系统用户
                  </p>
                </div>
                <span className="pointer-events-none absolute top-6 right-6 text-gray-300 group-hover:text-gray-400">
                  <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20 4h1a1 1 0 00-1-1v1zm-1 12a1 1 0 102 0h-2zM8 3a1 1 0 000 2V3zM3.293 19.293a1 1 0 101.414 1.414l-1.414-1.414zM19 4v12h2V4h-2zm1-1H8v2h12V3zm-.707.293l-16 16 1.414 1.414 16-16L19.293 3.293z"/>
                  </svg>
                </span>
              </Link>

              <Link
                href="/admin/users?role=admin"
                className="relative group bg-white p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-purple-500 rounded-lg border border-gray-200 hover:border-gray-300"
              >
                <div>
                  <span className="rounded-lg inline-flex p-3 bg-purple-50 text-purple-600 ring-4 ring-white">
                    <ShieldCheckIcon className="h-6 w-6" />
                  </span>
                </div>
                <div className="mt-4">
                  <h3 className="text-lg font-medium text-gray-900">
                    管理员设置
                  </h3>
                  <p className="mt-2 text-sm text-gray-500">
                    管理系统管理员权限
                  </p>
                </div>
                <span className="pointer-events-none absolute top-6 right-6 text-gray-300 group-hover:text-gray-400">
                  <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20 4h1a1 1 0 00-1-1v1zm-1 12a1 1 0 102 0h-2zM8 3a1 1 0 000 2V3zM3.293 19.293a1 1 0 101.414 1.414l-1.414-1.414zM19 4v12h2V4h-2zm1-1H8v2h12V3zm-.707.293l-16 16 1.414 1.414 16-16L19.293 3.293z"/>
                  </svg>
                </span>
              </Link>

              <div className="relative group bg-white p-6 rounded-lg border border-gray-200">
                <div>
                  <span className="rounded-lg inline-flex p-3 bg-green-50 text-green-600 ring-4 ring-white">
                    <TrendingUpIcon className="h-6 w-6" />
                  </span>
                </div>
                <div className="mt-4">
                  <h3 className="text-lg font-medium text-gray-900">
                    系统健康
                  </h3>
                  <p className="mt-2 text-sm text-gray-500">
                    {stats.active_users > 0 ? '系统运行正常' : '需要注意'}
                  </p>
                  <div className="mt-2 text-xs text-gray-400">
                    活跃率: {stats.total_users > 0 ? Math.round((stats.active_users / stats.total_users) * 100) : 0}%
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 数据分析图表区域 (占位) */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              趋势分析
            </h3>
            <div className="bg-gray-50 rounded-lg p-8 text-center">
              <TrendingUpIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">图表功能</h3>
              <p className="mt-1 text-sm text-gray-500">
                用户注册趋势图表功能正在开发中
              </p>
            </div>
          </div>
        </div>
      </div>
    </AdminLayout>
  )
}