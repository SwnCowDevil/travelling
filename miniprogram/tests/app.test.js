const test = require('node:test')
const assert = require('node:assert/strict')

test('local authentication can retry after the backend starts', async () => {
  let definition
  let attempts = 0
  const originalApp = global.App
  const originalWx = global.wx
  global.App = value => { definition = value }
  global.wx = {
    getStorageSync: () => '',
    setStorageSync() {},
    showToast() {},
    request(options) {
      attempts += 1
      if (attempts === 1) options.fail({ errMsg: 'request:fail backend offline' })
      else options.success({ statusCode: 200, data: { access_token: 'dev-token' } })
    }
  }
  delete require.cache[require.resolve('../miniprogram/app')]
  require('../miniprogram/app')

  const app = { globalData: { ...definition.globalData }, ensureAuthenticated: definition.ensureAuthenticated }
  definition.onLaunch.call(app)
  assert.equal(await app.globalData.authReady, false)
  assert.equal(await definition.ensureAuthenticated.call(app), true)
  assert.equal(attempts, 2)

  global.App = originalApp
  global.wx = originalWx
})
