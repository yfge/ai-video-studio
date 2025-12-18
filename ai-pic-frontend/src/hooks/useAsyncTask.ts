/**
 * useAsyncTask Hook
 *
 * Manages async task state (loading/error/data) with automatic error handling.
 *
 * Usage:
 * ```tsx
 * const task = useAsyncTask<User[]>()
 *
 * async function loadUsers() {
 *   await task.run(async () => {
 *     const response = await fetch('/api/users')
 *     return response.json()
 *   })
 * }
 *
 * if (task.loading) return <Spinner />
 * if (task.error) return <Error message={task.error.message} />
 * return <UserList users={task.data} />
 * ```
 */

import { useState, useCallback } from 'react'

export interface UseAsyncTaskReturn<T> {
  /**
   * Whether the task is currently running
   */
  loading: boolean
  /**
   * Error from the last failed task
   */
  error: Error | null
  /**
   * Data from the last successful task
   */
  data: T | null
  /**
   * Run an async task and update state
   */
  run: (task: () => Promise<T>) => Promise<T | null>
  /**
   * Reset state to initial values
   */
  reset: () => void
  /**
   * Set data directly (useful for optimistic updates)
   */
  setData: (data: T | null) => void
  /**
   * Set error directly
   */
  setError: (error: Error | null) => void
}

/**
 * Hook for managing async task state
 *
 * @template T - Type of data returned by the task
 * @param onError - Optional error handler
 * @returns Task state and control functions
 *
 * @example
 * const userTask = useAsyncTask<User>(
 *   (error) => console.error('Failed to load user:', error)
 * )
 *
 * // Run task
 * await userTask.run(() => api.getUser(id))
 *
 * // Check state
 * if (userTask.loading) return <Spinner />
 * if (userTask.error) return <Error />
 * if (userTask.data) return <UserProfile user={userTask.data} />
 *
 * @example
 * // With optimistic updates
 * const deleteTask = useAsyncTask<void>()
 *
 * async function deleteUser(id: number) {
 *   // Optimistically update UI
 *   const updatedUsers = users.filter(u => u.id !== id)
 *   setUsers(updatedUsers)
 *
 *   // Run delete
 *   await deleteTask.run(() => api.deleteUser(id))
 *     .catch(() => {
 *       // Rollback on error
 *       setUsers(users)
 *     })
 * }
 */
export function useAsyncTask<T>(
  onError?: (error: Error) => void
): UseAsyncTaskReturn<T> {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [data, setData] = useState<T | null>(null)

  const run = useCallback(
    async (task: () => Promise<T>): Promise<T | null> => {
      setLoading(true)
      setError(null)

      try {
        const result = await task()
        setData(result)
        return result
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err))
        setError(error)

        if (onError) {
          onError(error)
        }

        return null
      } finally {
        setLoading(false)
      }
    },
    [onError]
  )

  const reset = useCallback(() => {
    setLoading(false)
    setError(null)
    setData(null)
  }, [])

  return {
    loading,
    error,
    data,
    run,
    reset,
    setData,
    setError,
  }
}
