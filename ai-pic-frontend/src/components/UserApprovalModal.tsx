'use client'

import React, { useState } from 'react'
import { adminAPI, type AdminUser } from '../utils/api'

// Icons
const XIcon = ({ className = '' }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
)

const CheckIcon = ({ className = '' }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
  </svg>
)

const ExclamationIcon = ({ className = '' }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
  </svg>
)

const UserIcon = ({ className = '' }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
  </svg>
)

interface UserApprovalModalProps {
  user: AdminUser | null
  isOpen: boolean
  onClose: () => void
  onApprovalComplete: (user: AdminUser, action: 'approved' | 'rejected') => void
}

// Predefined approval/rejection reasons
const APPROVAL_REASONS = [
  '资料完整，符合注册要求',
  '通过人工审核验证',
  '邮箱验证通过',
  '身份信息确认无误',
  '符合平台使用条件',
  '其他'
]

const REJECTION_REASONS = [
  '提供信息不完整或不准确',
  '邮箱无效或无法验证',
  '违反平台注册条款',
  '疑似虚假注册信息',
  '重复注册账户',
  '不符合平台使用条件',
  '其他'
]

export default function UserApprovalModal({ 
  user, 
  isOpen, 
  onClose, 
  onApprovalComplete 
}: UserApprovalModalProps) {
  const [action, setAction] = useState<'approve' | 'reject' | null>(null)
  const [selectedReason, setSelectedReason] = useState('')
  const [customReason, setCustomReason] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset form when modal opens/closes
  React.useEffect(() => {
    if (isOpen) {
      setAction(null)
      setSelectedReason('')
      setCustomReason('')
      setError(null)
    }
  }, [isOpen, user])

  const handleActionSelect = (selectedAction: 'approve' | 'reject') => {
    setAction(selectedAction)
    setSelectedReason('')
    setCustomReason('')
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!user || !action) return
    
    const finalReason = selectedReason === '其他' ? customReason : selectedReason
    
    if (!finalReason.trim()) {
      setError('请选择或输入处理原因')
      return
    }
    
    setIsProcessing(true)
    setError(null)
    
    try {
      const response = await adminAPI.approveUser(user.id, {
        action: action,
        reason: finalReason
      })
      
      if (response.success && response.data) {
        onApprovalComplete(response.data, action === 'approve' ? 'approved' : 'rejected')
        onClose()
      } else {
        setError(response.error || '操作失败')
      }
    } catch (err) {
      setError('操作失败，请稍后重试')
      console.error('用户审批失败:', err)
    } finally {
      setIsProcessing(false)
    }
  }

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN')
  }

  const getUserStatusInfo = (user: AdminUser) => {
    if (!user.email_verified) {
      return {
        status: '邮箱未验证',
        color: 'text-orange-600 bg-orange-100',
        icon: ExclamationIcon
      }
    }
    if (!user.is_approved) {
      return {
        status: '待审批',
        color: 'text-yellow-600 bg-yellow-100',
        icon: ExclamationIcon
      }
    }
    if (!user.is_active) {
      return {
        status: '已暂停',
        color: 'text-red-600 bg-red-100',
        icon: ExclamationIcon
      }
    }
    return {
      status: '正常',
      color: 'text-green-600 bg-green-100',
      icon: CheckIcon
    }
  }

  if (!isOpen || !user) return null

  const statusInfo = getUserStatusInfo(user)

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
              <UserIcon className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-900">用户审批</h3>
              <p className="text-sm text-gray-500">处理用户注册申请</p>
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
                <label className="text-sm font-medium text-gray-500">全名</label>
                <p className="mt-1 text-sm text-gray-900">{user.full_name || '-'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">当前状态</label>
                <div className="mt-1">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusInfo.color}`}>
                    <statusInfo.icon className="w-3 h-3 mr-1" />
                    {statusInfo.status}
                  </span>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">注册时间</label>
                <p className="mt-1 text-sm text-gray-900">{formatDateTime(user.created_at)}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">登录失败次数</label>
                <p className="mt-1 text-sm text-gray-900">{user.failed_login_attempts || 0} 次</p>
              </div>
            </div>
          </div>

          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Action Selection */}
            <div>
              <label className="text-base font-medium text-gray-900">处理决定</label>
              <p className="text-sm leading-5 text-gray-500">选择如何处理此用户的注册申请</p>
              <fieldset className="mt-4">
                <div className="space-y-4 sm:flex sm:items-center sm:space-y-0 sm:space-x-10">
                  <div className="flex items-center">
                    <input
                      id="approve"
                      name="action"
                      type="radio"
                      checked={action === 'approve'}
                      onChange={() => handleActionSelect('approve')}
                      className="h-4 w-4 border-gray-300 text-green-600 focus:ring-green-500"
                      disabled={isProcessing}
                    />
                    <label htmlFor="approve" className="ml-3 block text-sm font-medium text-gray-700">
                      <span className="flex items-center">
                        <CheckIcon className="h-4 w-4 text-green-500 mr-2" />
                        批准用户
                      </span>
                    </label>
                  </div>
                  <div className="flex items-center">
                    <input
                      id="reject"
                      name="action"
                      type="radio"
                      checked={action === 'reject'}
                      onChange={() => handleActionSelect('reject')}
                      className="h-4 w-4 border-gray-300 text-red-600 focus:ring-red-500"
                      disabled={isProcessing}
                    />
                    <label htmlFor="reject" className="ml-3 block text-sm font-medium text-gray-700">
                      <span className="flex items-center">
                        <XIcon className="h-4 w-4 text-red-500 mr-2" />
                        拒绝用户
                      </span>
                    </label>
                  </div>
                </div>
              </fieldset>
            </div>

            {/* Reason Selection */}
            {action && (
              <div>
                <label htmlFor="reason" className="block text-sm font-medium text-gray-700">
                  {action === 'approve' ? '批准原因' : '拒绝原因'}
                  <span className="text-red-500 ml-1">*</span>
                </label>
                <select
                  id="reason"
                  value={selectedReason}
                  onChange={(e) => setSelectedReason(e.target.value)}
                  className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
                  disabled={isProcessing}
                >
                  <option value="">请选择原因...</option>
                  {(action === 'approve' ? APPROVAL_REASONS : REJECTION_REASONS).map((reason) => (
                    <option key={reason} value={reason}>
                      {reason}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Custom Reason Input */}
            {selectedReason === '其他' && (
              <div>
                <label htmlFor="customReason" className="block text-sm font-medium text-gray-700">
                  请说明具体原因
                  <span className="text-red-500 ml-1">*</span>
                </label>
                <textarea
                  id="customReason"
                  rows={3}
                  value={customReason}
                  onChange={(e) => setCustomReason(e.target.value)}
                  className="mt-1 block w-full sm:text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="请输入具体的处理原因..."
                  disabled={isProcessing}
                />
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
            disabled={!action || !selectedReason || (selectedReason === '其他' && !customReason.trim()) || isProcessing}
            className={`px-4 py-2 text-sm font-medium text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed ${
              action === 'approve' 
                ? 'bg-green-600 hover:bg-green-700' 
                : action === 'reject'
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-gray-400'
            }`}
          >
            {isProcessing ? (
              <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                处理中...
              </span>
            ) : (
              `确认${action === 'approve' ? '批准' : '拒绝'}`
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
