/**
 * API Endpoints Index
 *
 * Barrel export for all domain-specific API endpoint modules.
 */

// Auth endpoints
export * from "./auth.endpoints";

// Admin/User management endpoints
export * from "./admin.endpoints";

// Task endpoints
export * from "./task.endpoints";
export * from "./workbench.endpoints";

// Image generation profiles endpoints
export * from "./image-gen.endpoints";

// Voice/TTS endpoints
export * from "./voice.endpoints";

// Virtual IP endpoints
export * from "./virtual-ip.endpoints";

// Virtual IP Image endpoints
export * from "./virtual-ip-image.endpoints";

// Story endpoints
export * from "./story.endpoints";
export * from "./story-novel.endpoints";

// Episode endpoints
export * from "./episode.endpoints";
export * from "./episode-character.endpoints";
export * from "./timeline.endpoints";

// Script endpoints (includes storyboard)
export * from "./script.endpoints";

// Story structure endpoints (scenes, beats, shots, environments)
export * from "./story-structure.endpoints";

// AI model endpoints
export * from "./ai.endpoints";

// Style endpoints
export * from "./style.endpoints";
