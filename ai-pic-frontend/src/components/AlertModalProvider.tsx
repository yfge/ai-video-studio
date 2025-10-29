'use client'

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'

type AlertVariant = 'success' | 'error' | 'info' | 'warning'

export interface AlertOptions {
  title?: string
  message: string
  variant?: AlertVariant
  confirmText?: string
  onConfirm?: () => void
}

interface AlertContextValue {
  showAlert: (options: AlertOptions) => void
}

const AlertModalContext = createContext<AlertContextValue | undefined>(undefined)

const VariantIcon = ({ variant }: { variant: AlertVariant }) => {
  const baseProps = { className: 'h-6 w-6', strokeWidth: 1.8 }
  switch (variant) {
    case 'success':
      return (
        <svg {...baseProps} viewBox="0 0 24 24" fill="none" stroke="currentColor" className={`${baseProps.className} text-green-600`}>
          <path d="M9 12l2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="12" cy="12" r="9" />
        </svg>
      )
    case 'error':
      return (
        <svg {...baseProps} viewBox="0 0 24 24" fill="none" stroke="currentColor" className={`${baseProps.className} text-red-600`}>
          <path d="M9 9l6 6m0-6l-6 6" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="12" cy="12" r="9" />
        </svg>
      )
    case 'warning':
      return (
        <svg {...baseProps} viewBox="0 0 24 24" fill="none" stroke="currentColor" className={`${baseProps.className} text-amber-500`}>
          <path d="M12 8v4m0 4h.01" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M12 3l9 18H3l9-18z" />
        </svg>
      )
    case 'info':
    default:
      return (
        <svg {...baseProps} viewBox="0 0 24 24" fill="none" stroke="currentColor" className={`${baseProps.className} text-blue-600`}>
          <circle cx="12" cy="12" r="9" />
          <path d="M12 8h.01M11 12h1v4h1" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      )
  }
}

export function AlertModalProvider({ children }: { children: ReactNode }) {
  const [alertState, setAlertState] = useState<AlertOptions | null>(null)

  const showAlert = useCallback((options: AlertOptions) => {
    setAlertState({
      confirmText: '确定',
      variant: 'info',
      ...options,
    })
  }, [])

  const contextValue = useMemo(() => ({ showAlert }), [showAlert])

  const handleClose = useCallback(() => {
    setAlertState(null)
  }, [])

  const handleConfirm = useCallback(() => {
    alertState?.onConfirm?.()
    setAlertState(null)
  }, [alertState])

  const variant = alertState?.variant ?? 'info'
  const borderClass =
    variant === 'success'
      ? 'border-green-100'
      : variant === 'error'
        ? 'border-red-100'
        : variant === 'warning'
          ? 'border-amber-100'
          : 'border-blue-100'

  return (
    <AlertModalContext.Provider value={contextValue}>
      {children}
      {alertState ? (
        <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div
            className={`mx-4 w-full max-w-sm rounded-xl border bg-white p-6 shadow-2xl transition-all ${borderClass}`}
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="alert-modal-title"
            aria-describedby="alert-modal-description"
          >
            <div className="flex items-start gap-3">
              <VariantIcon variant={variant} />
              <div className="flex-1">
                <h2 id="alert-modal-title" className="text-lg font-semibold text-gray-900">
                  {alertState.title ?? (variant === 'success' ? '操作成功' : variant === 'error' ? '操作失败' : '提醒')}
                </h2>
                <p id="alert-modal-description" className="mt-2 text-sm text-gray-600 whitespace-pre-line">
                  {alertState.message}
                </p>
              </div>
            </div>
            <div className="mt-5 flex justify-end gap-3">
              <button
                type="button"
                onClick={handleClose}
                className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                取消
              </button>
              <button
                type="button"
                onClick={handleConfirm}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                {alertState.confirmText ?? '确定'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </AlertModalContext.Provider>
  )
}

export function useAlertModal() {
  const context = useContext(AlertModalContext)
  if (!context) {
    throw new Error('useAlertModal 必须在 AlertModalProvider 内使用')
  }
  return context
}
