'use client'

import React, { useState } from 'react'
import { adminAPI, type AdminUser } from '../utils/api'

// Icons
const XIcon = ({ className = '' }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
)

const ShieldIcon = ({ className = '' }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
  </svg>
)

const UserIcon = ({ className = '' }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
  </svg>
)

const CrownIcon = ({ className = '' }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
  </svg>
)

interface RoleManagementModalProps {
  user: AdminUser | null
  isOpen: boolean
  onClose: () => void
  onRoleUpdate: (user: AdminUser) => void
}

// Role definitions with descriptions
const ROLES = [
  {
    key: 'user',
    name: '普通用户',
    description: '基础用户权限，可使用平台核心功能',
    icon: UserIcon,
    color: 'text-gray-600 bg-gray-100',
    permissions: [
      '创建和管理Virtual IP',
      '生成AI图片和视频',
      '创建故事和剧本',
      '查看个人数据统计'
    ]
  },
  {
    key: 'admin',
    name: '管理员',
    description: '系统管理权限，可管理用户和系统设置',
    icon: ShieldIcon,
    color: 'text-blue-600 bg-blue-100',
    permissions: [
      '所有普通用户权限',
      '用户管理和审批',
      '系统设置配置',
      '查看系统统计',
      '审计日志查看'
    ]
  },
  {
    key: 'superuser',
    name: '超级管理员',
    description: '最高权限，可执行所有系统操作',
    icon: CrownIcon,
    color: 'text-purple-600 bg-purple-100',
    permissions: [
      '所有管理员权限',
      '系统级配置修改',
      '数据库直接操作',
      '系统维护和备份',
      '其他管理员权限管理'
    ]
  }
]

export default function RoleManagementModal({ 
  user, 
  isOpen, 
  onClose, 
  onRoleUpdate 
}: RoleManagementModalProps) {
  const [selectedRole, setSelectedRole] = useState<string>('')
  const [reason, setReason] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset form when modal opens/closes
  React.useEffect(() => {
    if (isOpen && user) {
      // Determine current role
      let currentRole = 'user'
      if (user.is_admin && user.username === 'admin') {
        currentRole = 'superuser'  // Special case for main admin user
      } else if (user.is_admin) {
        currentRole = 'admin'
      }
      setSelectedRole(currentRole)
      setReason('')
      setError(null)
    }
  }, [isOpen, user])

  const getCurrentRole = (user: AdminUser) => {
    if (user.is_admin && user.username === 'admin') {
      return ROLES.find(r => r.key === 'superuser') || ROLES[0]
    } else if (user.is_admin) {
      return ROLES.find(r => r.key === 'admin') || ROLES[0]
    }
    return ROLES.find(r => r.key === 'user') || ROLES[0]
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!user || !selectedRole) return
    
    const currentRole = getCurrentRole(user)
    if (currentRole.key === selectedRole) {
      setError('用户角色未发生变化')
      return
    }
    
    if (!reason.trim()) {
      setError('请输入角色变更原因')
      return
    }
    
    setIsProcessing(true)
    setError(null)
    
    try {
      const roleData = {
        is_admin: selectedRole === 'admin' || selectedRole === 'superuser',
        role_change_reason: reason
      }
      
      const response = await adminAPI.updateUserRole(user.id, roleData)
      
      if (response.success && response.data) {
        onRoleUpdate(response.data)
        onClose()
      } else {
        setError(response.error || '角色更新失败')
      }
    } catch (err) {
      setError('操作失败，请稍后重试')
      console.error('角色更新失败:', err)
    } finally {
      setIsProcessing(false)
    }
  }

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN')
  }

  if (!isOpen || !user) return null

  const currentRole = getCurrentRole(user)

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 bg-purple-100 rounded-full flex items-center justify-center">
              <ShieldIcon className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-900">角色管理</h3>
              <p className="text-sm text-gray-500">管理用户权限和角色</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            disabled={isProcessing}
          >
            <XIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* User Information */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h4 className="text-md font-medium text-gray-900 mb-3">用户信息</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500">用户名</label>
                <p className="mt-1 text-sm text-gray-900">{user.username}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">邮箱地址</label>
                <p className="mt-1 text-sm text-gray-900">{user.email}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">当前角色</label>
                <div className="mt-1">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${currentRole.color}`}>
                    <currentRole.icon className="w-3 h-3 mr-1" />
                    {currentRole.name}
                  </span>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">注册时间</label>
                <p className="mt-1 text-sm text-gray-900">{formatDateTime(user.created_at)}</p>
              </div>
            </div>
          </div>

          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Role Selection */}
            <div>
              <label className="text-base font-medium text-gray-900">选择新角色</label>
              <p className="text-sm leading-5 text-gray-500 mb-4">请谨慎选择用户角色，这将影响用户的系统权限</p>
              
              <div className="space-y-4">
                {ROLES.map((role) => (
                  <div key={role.key} className="relative">
                    <div className="flex items-start">
                      <div className="flex items-center h-5">
                        <input
                          id={role.key}
                          name="role"
                          type="radio"
                          checked={selectedRole === role.key}
                          onChange={(e) => setSelectedRole(e.target.value)}
                          value={role.key}
                          className="h-4 w-4 border-gray-300 text-purple-600 focus:ring-purple-500"
                          disabled={isProcessing}
                        />
                      </div>
                      <div className="ml-3 flex-1">
                        <label htmlFor={role.key} className="block text-sm font-medium text-gray-700">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${role.color} mr-2`}>
                            <role.icon className="w-3 h-3 mr-1" />
                            {role.name}
                          </span>
                          {currentRole.key === role.key && (
                            <span className="text-xs text-blue-600 font-medium ml-1">(当前)</span>
                          )}
                        </label>
                        <p className="text-sm text-gray-500 mt-1">{role.description}</p>
                        
                        {/* Permissions List */}
                        <div className="mt-2">
                          <p className="text-xs font-medium text-gray-600 mb-1">权限包括:</p>
                          <ul className="text-xs text-gray-500 list-disc list-inside space-y-0.5 ml-2">
                            {role.permissions.map((permission, index) => (
                              <li key={index}>{permission}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Reason Input */}
            <div>
              <label htmlFor="reason" className="block text-sm font-medium text-gray-700">
                角色变更原因
                <span className="text-red-500 ml-1">*</span>
              </label>
              <textarea
                id="reason"
                rows={3}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="mt-1 block w-full sm:text-sm border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                placeholder="请说明角色变更的原因和必要性..."
                disabled={isProcessing}
              />
              <p className="mt-1 text-xs text-gray-500">
                角色变更将被记录到审计日志中，请详细说明变更原因
              </p>
            </div>

            {/* Warning for sensitive operations */}
            {(selectedRole === 'admin' || selectedRole === 'superuser') && currentRole.key === 'user' && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-yellow-800">
                      重要提醒
                    </h3>
                    <div className="mt-2 text-sm text-yellow-700">
                      <p>
                        您正在将普通用户提升为{selectedRole === 'admin' ? '管理员' : '超级管理员'}。
                        此操作将授予该用户重要的系统权限，请确保用户可信且有相应的管理能力。
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {selectedRole === 'user' && currentRole.key !== 'user' && (
              <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-blue-800">
                      权限降级说明
                    </h3>
                    <div className="mt-2 text-sm text-blue-700">
                      <p>
                        此操作将撤销用户的管理权限，用户将只能访问普通用户功能。
                        请确保此变更不会影响正在进行的管理工作。
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </form>
        </div>

        {/* Footer */}
        <div className="flex justify-end space-x-3 px-6 py-4 border-t">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            disabled={isProcessing}
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            disabled={!selectedRole || !reason.trim() || currentRole.key === selectedRole || isProcessing}
            className="px-4 py-2 text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isProcessing ? (
              <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                更新中...
              </span>
            ) : (
              '确认更新角色'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
