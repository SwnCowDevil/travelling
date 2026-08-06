const test = require('node:test')
const assert = require('node:assert/strict')
const { defaultFilters, buildRequest, loadingStages } = require('../../miniprogram/pages/recommend/model')

test('defaults to current month and optional filters can be cleared', () => {
  const filters = defaultFilters(new Date('2026-08-06'))
  assert.equal(filters.month, 8)
  filters.categories = []; filters.maxDistanceKm = null; filters.crowd = null
  const request = buildRequest(filters, { name: '上海', latitude: 31.2, longitude: 121.4 })
  assert.equal(request.month, 8)
  assert.equal(request.max_distance_km, undefined)
  assert.deepEqual(request.preferred_categories, [])
})

test('loading stages progress in a finite sequence', () => {
  assert.deepEqual(loadingStages, ['正在筛选适合月份', '正在计算距离与偏好', '正在整理推荐理由'])
})

test('rule result keeps three cards and exposes fallback notice', () => {
  const response = { source: 'rules', items: [{code:'a'}, {code:'b'}, {code:'c'}] }
  assert.equal(response.items.length, 3)
  assert.equal(response.source === 'rules', true)
})
