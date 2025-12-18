/**
 * useModal Hook
 *
 * Manages modal state (open/close/data) with a simple interface.
 *
 * Usage:
 * ```tsx
 * const editModal = useModal<User>()
 *
 * // Open modal with data
 * <Button onClick={() => editModal.open(user)}>Edit</Button>
 *
 * // Render modal
 * <Modal
 *   isOpen={editModal.isOpen}
 *   onClose={editModal.close}
 * >
 *   {editModal.data && <EditForm user={editModal.data} />}
 * </Modal>
 * ```
 */

import { useState, useCallback } from 'react'

export interface UseModalReturn<T = undefined> {
  /**
   * Whether the modal is currently open
   */
  isOpen: boolean
  /**
   * Optional data associated with the modal
   */
  data: T | undefined
  /**
   * Open the modal with optional data
   */
  open: (data?: T) => void
  /**
   * Close the modal and clear data
   */
  close: () => void
  /**
   * Toggle modal state
   */
  toggle: () => void
  /**
   * Update data without changing open state
   */
  setData: (data: T | undefined) => void
}

/**
 * Hook for managing modal state
 *
 * @template T - Type of data associated with the modal
 * @param initialOpen - Initial open state (default: false)
 * @returns Modal state and control functions
 *
 * @example
 * // Simple modal (no data)
 * const confirmModal = useModal()
 * confirmModal.open()
 * confirmModal.close()
 *
 * @example
 * // Modal with data
 * const editModal = useModal<User>()
 * editModal.open(selectedUser)
 * console.log(editModal.data) // User object
 */
export function useModal<T = undefined>(
  initialOpen = false
): UseModalReturn<T> {
  const [isOpen, setIsOpen] = useState(initialOpen)
  const [data, setData] = useState<T | undefined>(undefined)

  const open = useCallback((newData?: T) => {
    setData(newData)
    setIsOpen(true)
  }, [])

  const close = useCallback(() => {
    setIsOpen(false)
    // Clear data after modal close animation (300ms typical)
    setTimeout(() => setData(undefined), 300)
  }, [])

  const toggle = useCallback(() => {
    setIsOpen((prev) => !prev)
  }, [])

  return {
    isOpen,
    data,
    open,
    close,
    toggle,
    setData,
  }
}
