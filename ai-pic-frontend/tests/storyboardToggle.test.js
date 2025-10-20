import test from 'node:test'
import assert from 'node:assert/strict'

import { selectUiScenes, initialSelectedSceneNumber, mapNormalizedSceneToSelected } from '../src/utils/storyboardToggle.js'

test('selectUiScenes returns raw or normalized based on toggle', () => {
  const normalized = [{ id: 1, scene_number: '3' }]
  const raw = [{}, {}, {}]
  assert.equal(selectUiScenes(false, normalized, raw).length, 3)
  assert.equal(selectUiScenes(true, normalized, raw).length, 1)
})

test('initialSelectedSceneNumber picks first normalized scene_number when available', () => {
  assert.equal(initialSelectedSceneNumber(true, [{ scene_number: '2' }], []), 2)
  assert.equal(initialSelectedSceneNumber(true, [{ scene_number: 'x' }], []), 1)
  assert.equal(initialSelectedSceneNumber(true, [], []), 1)
  assert.equal(initialSelectedSceneNumber(false, [], [{}]), 1)
})

test('mapNormalizedSceneToSelected normalizes numeric and string values', () => {
  assert.equal(mapNormalizedSceneToSelected({ scene_number: '5' }), 5)
  assert.equal(mapNormalizedSceneToSelected({ scene_number: 4 }), 4)
  assert.equal(mapNormalizedSceneToSelected({ scene_number: 'NaN' }), 1)
  assert.equal(mapNormalizedSceneToSelected(null), 1)
})

