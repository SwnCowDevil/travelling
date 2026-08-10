const test = require('node:test')
const assert = require('node:assert/strict')
const path = require('node:path')

const pagePath = path.join(__dirname, '../../miniprogram/pages/destination-detail/index.js')

function loadPage() {
  const originalPage = global.Page
  let definition
  global.Page = value => { definition = value }
  delete require.cache[require.resolve(pagePath)]
  require(pagePath)
  global.Page = originalPage
  return definition
}

function createPage(request) {
  const definition = loadPage()
  const page = {
    ...definition,
    data: { ...definition.data, view: { marker: 'old guide' } },
    guideContext: { api: { request }, id: 7, month: 8, days: 2, originName: '北京', preferences: ['景色'] },
    detailSource: {
      destination: { id: 7, name: '杭州西湖' },
      weather: { daily: [] }
    },
    setData(value) { this.data = { ...this.data, ...value } }
  }
  return page
}

test('regenerate sends force_refresh and replaces the displayed guide', async () => {
  let sent
  const page = createPage(async request => {
    sent = request
    return { source: 'ai', payload: { transport: ['高铁'], weather: ['晴'], packing: [], cautions: [], highlights: [], foods: [], itinerary: [] } }
  })
  const originalWx = global.wx
  global.wx = { showToast() {} }
  await page.regenerateGuide()
  global.wx = originalWx

  assert.equal(sent.data.force_refresh, true)
  assert.equal(sent.data.days, 2)
  assert.equal(sent.timeout, 120000)
  assert.equal(page.data.view.guideSourceLabel, 'AI 攻略')
  assert.equal(page.data.regenerating, false)
})

test('failed regenerate keeps the old guide and restores the button', async () => {
  const page = createPage(async () => { throw new Error('AI unavailable') })
  const oldView = page.data.view
  let toast
  const originalWx = global.wx
  global.wx = { showToast(value) { toast = value } }
  await page.regenerateGuide()
  global.wx = originalWx

  assert.equal(page.data.view, oldView)
  assert.equal(page.data.regenerating, false)
  assert.equal(toast.icon, 'none')
  assert.match(toast.title, /AI unavailable/)
})
