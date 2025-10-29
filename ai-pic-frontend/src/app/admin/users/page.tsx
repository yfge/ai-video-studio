'use client'

import React, { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import AdminLayout from '../../../components/AdminLayout'
import UserDetailsModal from '../../../components/UserDetailsModal'
import UserApprovalModal from '../../../components/UserApprovalModal'
import { adminAPI, AdminUser, UserListResponse } from '../../../utils/api'
import { getUserStatus, getUserStatusColor, getUserRole, getUserRoleColor, formatRelativeTime } from '../../../utils/auth'

interface UserFilters {
  page: number
  size: number
  status_filter?: string
  role_filter?: string
  search?: string
}

// 简单的图标组件
const SearchIcon = ({ className = '' }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
  </svg>
)

const CheckIcon = ({ className = '' }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
  </svg>
)

const XIcon = ({ className = '' }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
)

const DotsVerticalIcon = ({ className = '' }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
  </svg>
)

export default function AdminUsersPage() {
  const searchParams = useSearchParams()
  
  // 状态管理
  const [userList, setUserList] = useState<UserListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<UserFilters>({
    page: 1,
    size: 20,
    status_filter: searchParams.get('status') || undefined,
    role_filter: undefined,
    search: undefined,
  })
  
  // 操作状态
  const [processingUsers, setProcessingUsers] = useState<Set<number>>(new Set())
  // 用户详情模态框状态
  const [selectedUserForDetails, setSelectedUserForDetails] = useState<AdminUser | null>(null)
  const [showUserDetailsModal, setShowUserDetailsModal] = useState(false)
  
  // 用户审批模态框状态
  const [selectedUserForApproval, setSelectedUserForApproval] = useState<AdminUser | null>(null)
  const [showUserApprovalModal, setShowUserApprovalModal] = useState(false)

  // 加载用户列表
  const loadUsers = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await adminAPI.getUsers(filters)
      
      if (response.success && response.data) {
        setUserList(response.data)
      } else {
        setError(response.error || '获取用户列表失败')
      }
    } catch (err) {
      setError('网络错误，请稍后重试')
      console.error('加载用户列表失败:', err)
    } finally {
      setLoading(false)
    }
  }, [filters])

  // 初始加载和筛选变化时重新加载
  useEffect(() => {
    void loadUsers()
  }, [loadUsers])

  // 处理搜索
  const handleSearch = (searchTerm: string) => {
    setFilters(prev => ({
      ...prev,
      page: 1,
      search: searchTerm || undefined
    }))
  }

  // 处理筛选
  const handleFilterChange = (key: 'status_filter' | 'role_filter', value: string) => {
    setFilters(prev => ({
      ...prev,
      page: 1,
      [key]: value ? value : undefined
    }))
  }

  // 处理分页
  const handlePageChange = (page: number) => {
    setFilters(prev => ({ ...prev, page }))
  }

  // 手动验证邮箱
  const verifyEmail = async (user: AdminUser) => {
    try {
      setProcessingUsers(prev => new Set(prev).add(user.id))
      
      const response = await adminAPI.updateUserAdmin(user.id, {
        email_verified: true
      })
      
      if (response.success) {
        await loadUsers()
      } else {
        setError(response.error || '操作失败')
      }
    } catch (err) {
      setError('操作失败，请稍后重试')
      console.error('验证邮箱失败:', err)
    } finally {
      setProcessingUsers(prev => {
        const newSet = new Set(prev)
        newSet.delete(user.id)
        return newSet
      })
    }
  }

  // 用户详情模态框处理函数
  const handleOpenUserDetails = (user: AdminUser) => {
    setSelectedUserForDetails(user)
    setShowUserDetailsModal(true)
  }

  const handleCloseUserDetails = () => {
    setShowUserDetailsModal(false)
    setSelectedUserForDetails(null)
  }

  const handleUserUpdate = async (updatedUser: AdminUser) => {
    // 更新用户列表中的用户信息
    if (userList) {
      setUserList({
        ...userList,
        users: userList.users.map(user => 
          user.id === updatedUser.id ? updatedUser : user
        )
      })
    }
    // 如果详情模态框中的用户被更新，也更新详情模态框中的数据
    if (selectedUserForDetails && selectedUserForDetails.id === updatedUser.id) {
      setSelectedUserForDetails(updatedUser)
    }
  }

  // 用户审批模态框处理函数
  const handleOpenUserApproval = (user: AdminUser) => {
    setSelectedUserForApproval(user)
    setShowUserApprovalModal(true)
  }

  const handleCloseUserApproval = () => {
    setShowUserApprovalModal(false)
    setSelectedUserForApproval(null)
  }

  const handleApprovalComplete = (user: AdminUser, action: 'approved' | 'rejected') => {
    // 更新用户列表
    if (userList) {
      setUserList({
        ...userList,
        users: userList.users.map(u => 
          u.id === user.id ? user : u
        )
      })
    }
    
    // 显示成功消息
    console.log(`用户 ${user.username} 已${action === 'approved' ? '批准' : '拒绝'}`)
  }

  if (loading && !userList) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </AdminLayout>
    )
  }

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* 页面头部 */}
        <div className="sm:flex sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">用户管理</h1>
            <p className="mt-2 text-sm text-gray-700">
              管理系统用户的注册、审批和权限设置
            </p>
          </div>
        </div>

        {/* 搜索和筛选 */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* 搜索框 */}
            <div className="md:col-span-2">
              <div className="relative">
                <SearchIcon className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="搜索用户名、邮箱或姓名..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  value={filters.search || ''}
                  onChange={(e) => handleSearch(e.target.value)}
                />
              </div>
            </div>

            {/* 状态筛选 */}
            <div>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                value={filters.status_filter || ''}
                onChange={(e) => handleFilterChange('status_filter', e.target.value)}
              >
                <option value="">所有状态</option>
                <option value="pending">待审批</option>
                <option value="approved">已审批</option>
                <option value="suspended">已暂停</option>
                <option value="locked">已锁定</option>
              </select>
            </div>

            {/* 角色筛选 */}
            <div>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                value={filters.role_filter || ''}
                onChange={(e) => handleFilterChange('role_filter', e.target.value)}
              >
                <option value="">所有角色</option>
                <option value="admin">管理员</option>
                <option value="superuser">超级用户</option>
                <option value="user">普通用户</option>
              </select>
            </div>
          </div>

          {/* 统计信息 */}
          {userList && (
            <div className="mt-4 text-sm text-gray-500">
              共 {userList.total} 个用户，当前显示第 {userList.page} 页
            </div>
          )}
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="rounded-md bg-red-50 p-4">
            <div className="flex">
              <XIcon className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">{error}</h3>
              </div>
            </div>
          </div>
        )}

        {/* 用户列表 */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          {userList && userList.users.length > 0 ? (
            <ul className="divide-y divide-gray-200">
              {userList.users.map((user) => (
                <li key={user.id} className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      {/* 用户头像 */}
                      <div className="flex-shrink-0 h-10 w-10">
                        <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                          <span className="text-sm font-medium text-gray-700">
                            {user.username.charAt(0).toUpperCase()}
                          </span>
                        </div>
                      </div>

                      {/* 用户信息 */}
                      <div className="ml-4">
                        <div className="flex items-center space-x-2">
                          <h3 className="text-sm font-medium text-gray-900">
                            {user.full_name || user.username}
                          </h3>
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getUserStatusColor(user)} bg-opacity-10`}>
                            {getUserStatus(user)}
                          </span>
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getUserRoleColor(user)} bg-opacity-10`}>
                            {getUserRole(user)}
                          </span>
                        </div>
                        <div className="text-sm text-gray-500">
                          {user.email} • 注册于 {formatRelativeTime(user.created_at)}
                          {user.last_login_at && ` • 最后登录 ${formatRelativeTime(user.last_login_at)}`}
                        </div>
                        {user.failed_login_attempts > 0 && (
                          <div className="text-xs text-red-500 mt-1">
                            失败登录次数: {user.failed_login_attempts}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* 操作按钮 */}
                    <div className="flex items-center space-x-2">
                      {!user.is_approved && (
                        <button
                          onClick={() => handleOpenUserApproval(user)}
                          disabled={processingUsers.has(user.id)}
                          className="inline-flex items-center px-2.5 py-1.5 text-xs font-medium rounded text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 disabled:opacity-50"
                        >
                          <CheckIcon className="h-3 w-3 mr-1" />
                          处理审批
                        </button>
                      )}

                      {!user.email_verified && user.is_approved && (
                        <button
                          onClick={() => verifyEmail(user)}
                          disabled={processingUsers.has(user.id)}
                          className="inline-flex items-center px-2.5 py-1.5 text-xs font-medium rounded text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                        >
                          验证邮箱
                        </button>
                      )}

                      <button
                        onClick={() => handleOpenUserDetails(user)}
                        className="p-1 text-gray-400 hover:text-gray-500"
                        title="查看用户详情"
                      >
                        <DotsVerticalIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-center py-12">
              <p className="text-sm text-gray-500">没有找到符合条件的用户</p>
            </div>
          )}
        </div>

        {/* 分页 */}
        {userList && userList.pages > 1 && (
          <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={() => handlePageChange(Math.max(1, filters.page - 1))}
                disabled={filters.page <= 1}
                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                上一页
              </button>
              <button
                onClick={() => handlePageChange(Math.min(userList.pages, filters.page + 1))}
                disabled={filters.page >= userList.pages}
                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                下一页
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  显示 <span className="font-medium">{(filters.page - 1) * filters.size + 1}</span> 到{' '}
                  <span className="font-medium">
                    {Math.min(filters.page * filters.size, userList.total)}
                  </span>{' '}
                  共 <span className="font-medium">{userList.total}</span> 个结果
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                  <button
                    onClick={() => handlePageChange(Math.max(1, filters.page - 1))}
                    disabled={filters.page <= 1}
                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                  >
                    上一页
                  </button>
                  
                  {/* 页码按钮 */}
                  {Array.from({ length: Math.min(5, userList.pages) }, (_, i) => {
                    const page = i + Math.max(1, filters.page - 2)
                    if (page > userList.pages) return null
                    
                    return (
                      <button
                        key={page}
                        onClick={() => handlePageChange(page)}
                        className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                          page === filters.page
                            ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                            : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                        }`}
                      >
                        {page}
                      </button>
                    )
                  })}
                  
                  <button
                    onClick={() => handlePageChange(Math.min(userList.pages, filters.page + 1))}
                    disabled={filters.page >= userList.pages}
                    className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                  >
                    下一页
                  </button>
                </nav>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 用户详情模态框 */}
      <UserDetailsModal
        user={selectedUserForDetails}
        isOpen={showUserDetailsModal}
        onClose={handleCloseUserDetails}
        onUserUpdate={handleUserUpdate}
      />

      {/* 用户审批模态框 */}
      <UserApprovalModal
        user={selectedUserForApproval}
        isOpen={showUserApprovalModal}
        onClose={handleCloseUserApproval}
        onApprovalComplete={handleApprovalComplete}
      />
    </AdminLayout>
  )
}
