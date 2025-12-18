/**
 * API Types
 *
 * Re-exports all types from api.ts (temporary during Phase 0).
 * In Phase 2, types will be moved here and organized into logical modules.
 *
 * TODO (Phase 2):
 * - Move all types from api.ts to this directory
 * - Organize into modules: user.ts, story.ts, virtual-ip.ts, etc.
 * - Each module exports its domain types
 * - This index.ts becomes a barrel export
 */

// Temporary: Re-export from parent api.ts (../../api.ts from here)
export * from '../../api'
