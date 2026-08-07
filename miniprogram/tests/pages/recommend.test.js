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

test('recommendation waits for a missing origin and resumes after selection', async () => {
  let definition
  const originalPage = global.Page
  const originalWx = global.wx
  const originalGetApp = global.getApp
  global.Page = value => { definition = value }
  global.wx = { showToast() {} }
  global.getApp = () => ({ globalData: { api: { request: async () => ({ items: [], session_id: 1, source: 'rules' }) } } })
  delete require.cache[require.resolve('../../miniprogram/pages/recommend/index')]
  require('../../miniprogram/pages/recommend/index')

  let chooseCount = 0
  let requestCount = 0
  const page = {
    data: { origin: {}, filters: defaultFilters(new Date('2026-08-06')) },
    setData(value) { Object.assign(this.data, value) },
    selectComponent() { return { choose: () => { chooseCount += 1 } } }
  }
  page.recommend = definition.recommend
  global.getApp = () => ({ globalData: { api: { request: async () => { requestCount += 1; return { items: [], session_id: 1, source: 'rules' } } } } })

  await definition.recommend.call(page)
  assert.equal(chooseCount, 1)
  assert.equal(requestCount, 0)
  assert.equal(page.data.pendingRecommend, true)

  await definition.onOrigin.call(page, { detail: { name: '杭州', latitude: 30.2, longitude: 120.2 } })
  assert.equal(requestCount, 1)

  global.Page = originalPage
  global.wx = originalWx
  global.getApp = originalGetApp
})
