// Minimal pure helpers to support unit tests around the storyboard toggle logic

/**
 * Returns the UI scenes array based on the toggle state.
 * @param {boolean} useNormalized
 * @param {Array<{id:number, scene_number:string, slug_line?:string, status?:string}>} normalizedScenes
 * @param {Array<any>} rawScenes
 */
export function selectUiScenes(useNormalized, normalizedScenes, rawScenes) {
  return useNormalized ? (normalizedScenes || []) : (rawScenes || [])
}

/**
 * Compute initial selected scene number according to toggle and available scenes.
 * For normalized scenes, tries to parse the first scene's scene_number.
 * Falls back to 1 when not available or invalid.
 * @param {boolean} useNormalized
 * @param {Array<{scene_number:string}>} normalizedScenes
 * @param {Array<any>} rawScenes
 */
export function initialSelectedSceneNumber(useNormalized, normalizedScenes, rawScenes) {
  if (useNormalized) {
    const first = (normalizedScenes || [])[0]
    if (first && typeof first.scene_number === 'string') {
      const sn = parseInt(first.scene_number, 10)
      return Number.isFinite(sn) ? sn : 1
    }
    return 1
  }
  return (rawScenes && rawScenes.length > 0) ? 1 : 1
}

/**
 * Map a normalized scene object to the numeric scene index used by the existing storyboard frames.
 * @param {{scene_number?: string|number}|null} scene
 */
export function mapNormalizedSceneToSelected(scene) {
  if (!scene) return 1
  const v = scene.scene_number
  if (typeof v === 'number') return v
  if (typeof v === 'string') {
    const sn = parseInt(v, 10)
    return Number.isFinite(sn) ? sn : 1
  }
  return 1
}
