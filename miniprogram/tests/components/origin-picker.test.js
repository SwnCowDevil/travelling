const test = require('node:test')
const assert = require('node:assert/strict')

test('manual location failure is visible instead of being swallowed', async () => {
  let definition
  let toast
  const originalComponent = global.Component
  const originalWx = global.wx
  global.Component = value => { definition = value }
  global.wx = {
    chooseLocation: options => options.fail({ errMsg: 'chooseLocation:fail cancel' }),
    showToast: options => { toast = options }
  }
  delete require.cache[require.resolve('../../miniprogram/components/origin-picker/index')]
  require('../../miniprogram/components/origin-picker/index')

  await definition.methods.choose.call({ triggerEvent() {} })

  assert.equal(toast.icon, 'none')
  assert.match(toast.title, /出发地/)
  global.Component = originalComponent
  global.wx = originalWx
})
