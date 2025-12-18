'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { isAuthenticated } from '@/utils/auth'

interface AuthGuardProps {
  children: React.ReactNode
}

export default function AuthGuard({ children }: AuthGuardProps) {
  const [loading, setLoading] = useState(true)
  const [authenticated, setAuthenticated] = useState(false)
  const router = useRouter()

  useEffect(() => {
    const checkAuth = () => {
      const isAuth = isAuthenticated()
      
      if (!isAuth) {
        router.push('/login')
        return
      }
      
      setAuthenticated(true)
      setLoading(false)
    }

    checkAuth()
  }, [router])

  // 显示加载状态
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">检查登录状态...</p>
        </div>
      </div>
    )
  }

  // 未认证状态不渲染子组件
  if (!authenticated) {
    return null
  }

  // 已认证，渲染子组件
  return <>{children}</>
}