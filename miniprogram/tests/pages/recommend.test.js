const test = require('node:test')
const assert = require('node:assert/strict')
const {
  DAY_OPTIONS,
  defaultFilters,
  buildRequest,
  loadingStages,
  toggleFilter,
  setMonth,
  setDays,
  setDistanceRange,
  resetOptionalFilters,
  filterSummary,
  filterOptions
} = require('../../miniprogram/pages/recommend/model')

test('days filter toggles one quick option and maps it to recommendation context', () => {
  let filters = defaultFilters(new Date('2026-08-07'))
  assert.deepEqual(DAY_OPTIONS, [1, 2, 3, 5, 7])

  filters = setDays(filters, 3)
  assert.equal(filters.days, 3)
  assert.deepEqual(
    filterOptions(filters).days.filter(item => item.selected).map(item => item.value),
    [3]
  )
  assert.match(filterSummary(filters).map(item => item.label).join(','), /3天/)
  assert.equal(
    buildRequest(filters, { name: '上海', latitude: 31.2, longitude: 121.4 }).available_days,
    3
  )

  filters = setDays(filters, 3)
  assert.equal(filters.days, null)
  assert.equal(
    buildRequest(filters, { name: '上海', latitude: 31.2, longitude: 121.4 }).available_days,
    undefined
  )
  assert.equal(resetOptionalFilters(setDays(filters, 5)).days, null)
})

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

test('optional recommendation filters toggle independently', () => {
  let filters = defaultFilters(new Date('2026-08-07'))
  filters = toggleFilter(filters, 'categories', '山川')
  filters = toggleFilter(filters, 'categories', '古城')
  filters = toggleFilter(filters, 'preferences', '景色')
  assert.deepEqual(filters.categories, ['山川', '古城'])
  assert.deepEqual(filterSummary(filters).map(item => item.label), ['8月', '景色', '山川', '古城'])

  filters = toggleFilter(filters, 'categories', '山川')
  filters = setMonth(filters, 10)
  assert.deepEqual(filters.categories, ['古城'])
  assert.equal(filters.month, 10)

  filters = resetOptionalFilters(filters)
  assert.equal(filters.month, 10)
  assert.deepEqual(filters.preferences, [])
  assert.deepEqual(filters.categories, [])
})

test('distance range is single-select, summarized, and mapped to exact bounds', () => {
  let filters = defaultFilters(new Date('2026-08-07'))
  filters = setDistanceRange(filters, '100-200')
  const request = buildRequest(filters, { name: '上海', latitude: 31.2, longitude: 121.4 })

  assert.equal(filters.distanceRange, '100-200')
  assert.equal(request.min_distance_km, 100)
  assert.equal(request.max_distance_km, 200)
  assert.deepEqual(filterSummary(filters).map(item => item.label), ['8月', '100–200km'])
  assert.deepEqual(
    filterOptions(filters).distance.filter(item => item.selected).map(item => item.value),
    ['100-200']
  )

  filters = setDistanceRange(filters, null)
  const unlimited = buildRequest(filters, { name: '上海', latitude: 31.2, longitude: 121.4 })
  assert.equal(unlimited.min_distance_km, undefined)
  assert.equal(unlimited.max_distance_km, undefined)

  filters = resetOptionalFilters(setDistanceRange(filters, 'over-500'))
  assert.equal(filters.distanceRange, null)
})

test('preferences and destination categories share the backend category filter', () => {
  let filters = defaultFilters(new Date('2026-08-07'))
  filters = toggleFilter(filters, 'preferences', '人文')
  filters = toggleFilter(filters, 'categories', '古城')
  const request = buildRequest(filters, { name: '上海', latitude: 31.2, longitude: 121.4 })
  assert.deepEqual(request.preferred_categories, ['人文', '古城'])
})

test('request uses address when the selected origin name is blank', () => {
  const request = buildRequest(defaultFilters(new Date('2026-08-07')), {
    name: '  ', address: '北京市东城区东长安街', regionName: '北京市东城区',
    latitude: 39.9, longitude: 116.4
  })
  assert.equal(request.origin_name, '北京市东城区东长安街')
})

test('page selects and clears the distance range filter', () => {
  let definition
  const originalPage = global.Page
  global.Page = value => { definition = value }
  delete require.cache[require.resolve('../../miniprogram/pages/recommend/index')]
  require('../../miniprogram/pages/recommend/index')
  let refreshed
  const page = {
    data: { filters: defaultFilters(new Date('2026-08-07')) },
    refreshFilterView(filters) { refreshed = filters }
  }

  definition.selectDistanceRange.call(page, { currentTarget: { dataset: { value: '100-200' } } })
  assert.equal(refreshed.distanceRange, '100-200')

  page.data.filters = refreshed
  definition.removeSummary.call(page, { currentTarget: { dataset: { key: 'distanceRange', value: '100-200' } } })
  assert.equal(refreshed.distanceRange, null)
  global.Page = originalPage
})

test('page selects and clears the days filter', () => {
  let definition
  const originalPage = global.Page
  global.Page = value => { definition = value }
  delete require.cache[require.resolve('../../miniprogram/pages/recommend/index')]
  require('../../miniprogram/pages/recommend/index')
  let refreshed
  const page = {
    data: { filters: defaultFilters(new Date('2026-08-07')) },
    refreshFilterView(filters) { refreshed = filters }
  }

  definition.selectDays.call(page, { currentTarget: { dataset: { days: 5 } } })
  assert.equal(refreshed.days, 5)

  page.data.filters = refreshed
  definition.removeSummary.call(page, { currentTarget: { dataset: { key: 'days', value: 5 } } })
  assert.equal(refreshed.days, null)
  global.Page = originalPage
})

test('normal recommendation details inherit selected days and default to two', () => {
  let definition
  let navigatedUrl
  const originalPage = global.Page
  const originalWx = global.wx
  global.Page = value => { definition = value }
  global.wx = { navigateTo: ({ url }) => { navigatedUrl = url } }
  delete require.cache[require.resolve('../../miniprogram/pages/recommend/index')]
  require('../../miniprogram/pages/recommend/index')
  const page = { data: { filters: { ...defaultFilters(new Date('2026-08-07')), days: 5 } } }

  definition.openDetail.call(page, { detail: { id: 20 } })
  assert.match(navigatedUrl, /days=5/)

  page.data.filters.days = null
  definition.openDetail.call(page, { detail: { id: 20 } })
  assert.match(navigatedUrl, /days=2/)
  global.Page = originalPage
  global.wx = originalWx
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
    chooseOrigin() { chooseCount += 1 }
  }
  page.recommend = definition.recommend
  page.closeFilters = definition.closeFilters
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

test('page directly assigns and displays the selected origin', async () => {
  let definition
  const originalPage = global.Page
  const originalWx = global.wx
  const originalGetApp = global.getApp
  global.Page = value => { definition = value }
  global.wx = {
    chooseLocation: options => options.success({ name: '', address: '', latitude: 39.9, longitude: 116.4 }),
    setStorageSync() {}
  }
  global.getApp = () => ({ globalData: {
    authReady: Promise.resolve(true),
    api: { request: async () => ({
      name: '天安门', region_name: '北京市东城区', address: '北京市东城区东长安街',
      latitude: 39.9, longitude: 116.4, source: 'amap'
    }) }
  } })
  delete require.cache[require.resolve('../../miniprogram/pages/recommend/index')]
  require('../../miniprogram/pages/recommend/index')

  const page = {
    data: { origin: {}, pendingRecommend: false },
    setData(value) { Object.assign(this.data, value) },
    onOrigin: definition.onOrigin
  }
  await definition.chooseOrigin.call(page)

  assert.deepEqual(page.data.origin, {
    type: 'manual', name: '天安门', regionName: '北京市东城区',
    address: '北京市东城区东长安街', latitude: 39.9, longitude: 116.4, source: 'amap'
  })
  global.Page = originalPage
  global.wx = originalWx
  global.getApp = originalGetApp
})

test('late automatic location cannot overwrite a manual origin', async () => {
  let definition
  let finishAutoLocation
  const originalPage = global.Page
  const originalWx = global.wx
  global.Page = value => { definition = value }
  global.wx = {
    getStorageSync: () => null,
    getLocation: options => { finishAutoLocation = () => options.success({ latitude: 31.2, longitude: 121.4 }) }
  }
  delete require.cache[require.resolve('../../miniprogram/pages/recommend/index')]
  require('../../miniprogram/pages/recommend/index')

  const page = {
    data: { origin: {}, pendingRecommend: false },
    setData(value) { Object.assign(this.data, value) }
  }
  const loading = definition.onLoad.call(page)
  await definition.onOrigin.call(page, { detail: { type: 'manual', name: '西湖', latitude: 30.2, longitude: 120.1 } })
  finishAutoLocation()
  await loading

  assert.equal(page.data.origin.name, '西湖')
  global.Page = originalPage
  global.wx = originalWx
})

test('recommend and next keep AI and rule notices mutually exclusive', async () => {
  let definition
  const originalPage = global.Page
  const originalWx = global.wx
  const originalGetApp = global.getApp
  const responses = [
    { items: [{ code: 'ai' }], session_id: 9, has_more: true, source: 'ai' },
    { items: [{ code: 'rules' }], has_more: false, source: 'rules' }
  ]
  global.Page = value => { definition = value }
  global.wx = { showToast() {} }
  global.getApp = () => ({ globalData: {
    authReady: Promise.resolve(true),
    api: { request: async () => responses.shift() }
  } })
  delete require.cache[require.resolve('../../miniprogram/pages/recommend/index')]
  require('../../miniprogram/pages/recommend/index')

  const page = {
    data: {
      ...definition.data,
      origin: { name: '北京', latitude: 39.9, longitude: 116.4 },
      filters: defaultFilters(new Date('2026-08-07'))
    },
    setData(value) { Object.assign(this.data, value) },
    closeFilters: definition.closeFilters
  }

  await definition.recommend.call(page)
  assert.equal(page.data.aiGenerated, true)
  assert.equal(page.data.fallback, false)
  await definition.next.call(page)
  assert.equal(page.data.aiGenerated, false)
  assert.equal(page.data.fallback, true)

  global.Page = originalPage
  global.wx = originalWx
  global.getApp = originalGetApp
})

test('manual origin privacy denial does not redirect to system settings', async () => {
  let definition
  let toast
  let opened = false
  const originalPage = global.Page
  const originalWx = global.wx
  global.Page = value => { definition = value }
  global.wx = {
    getPrivacySetting: options => options.success({ needAuthorization: true }),
    requirePrivacyAuthorize: options => options.fail({ errMsg: 'privacy deny' }),
    chooseLocation: () => { throw new Error('must not call chooseLocation') },
    showToast: options => { toast = options },
    showModal() { throw new Error('must not show permission modal') },
    openSetting: () => { opened = true }
  }
  delete require.cache[require.resolve('../../miniprogram/pages/recommend/index')]
  require('../../miniprogram/pages/recommend/index')
  const page = {
    data: { resolvingOrigin: false },
    setData(value) { Object.assign(this.data, value) },
    onOriginCancel: definition.onOriginCancel
  }

  await definition.chooseOrigin.call(page)

  assert.match(toast.title, /隐私保护/)
  assert.equal(opened, false)
  global.Page = originalPage
  global.wx = originalWx
})
