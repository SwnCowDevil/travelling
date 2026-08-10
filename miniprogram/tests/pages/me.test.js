const test = require('node:test')
const assert = require('node:assert/strict')

test('profile counters aggregate map summary statuses safely', () => {
  const { toProfileStats } = require('../../miniprogram/pages/me/model')
  const summary = { items: [
    { status_counts: { visited: 2, revisit: 1, want: 3, avoid: 1 } },
    { status_counts: { visited: 1, want: 2, avoid: 1 } }
  ] }
  assert.deepEqual(toProfileStats(summary), { visited: 4, want: 5, avoid: 2, favorites: 0 })
  assert.deepEqual(toProfileStats({}, 3), { visited: 0, want: 0, avoid: 0, favorites: 3 })
})

test('profile navigation uses tab and page routes correctly', () => {
  let definition
  const calls = []
  const originalPage = global.Page
  const originalWx = global.wx
  global.Page = value => { definition = value }
  global.wx = {
    switchTab: options => calls.push(['tab', options.url]),
    navigateTo: options => calls.push(['page', options.url]),
    showToast: options => calls.push(['toast', options.title])
  }
  delete require.cache[require.resolve('../../miniprogram/pages/me/index')]
  require('../../miniprogram/pages/me/index')

  definition.openMap()
  definition.openVisits()
  definition.openFavorites()
  definition.openAI()
  definition.showComingSoon()

  assert.deepEqual(calls, [
    ['tab', '/pages/map/index'],
    ['page', '/pages/visit-records/index'],
    ['page', '/pages/favorite-guides/index'],
    ['page', '/pages/ai-settings/index'],
    ['toast', '敬请期待']
  ])
  global.Page = originalPage
  global.wx = originalWx
})
