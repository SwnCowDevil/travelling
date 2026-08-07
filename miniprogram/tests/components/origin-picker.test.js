const test = require('node:test')
const assert = require('node:assert/strict')

test('cancelling manual location emits cancel without an error toast', async () => {
  let definition
  let toast
  let event
  const originalComponent = global.Component
  const originalWx = global.wx
  global.Component = value => { definition = value }
  global.wx = {
    chooseLocation: options => options.fail({ errMsg: 'chooseLocation:fail cancel' }),
    showToast: options => { toast = options }
  }
  delete require.cache[require.resolve('../../miniprogram/components/origin-picker/index')]
  require('../../miniprogram/components/origin-picker/index')

  await definition.methods.choose.call({ triggerEvent: name => { event = name } })

  assert.equal(event, 'cancel')
  assert.equal(toast, undefined)
  global.Component = originalComponent
  global.wx = originalWx
})

test('permission denial offers to open settings', async () => {
  let definition
  let modal
  let opened = false
  const originalComponent = global.Component
  const originalWx = global.wx
  global.Component = value => { definition = value }
  global.wx = {
    chooseLocation: options => options.fail({ errMsg: 'chooseLocation:fail auth deny' }),
    showModal: options => { modal = options; options.success({ confirm: true }) },
    openSetting: options => { opened = true; options.success({ authSetting: { 'scope.userLocation': true } }) },
    showToast() {}
  }
  delete require.cache[require.resolve('../../miniprogram/components/origin-picker/index')]
  require('../../miniprogram/components/origin-picker/index')

  await definition.methods.choose.call({ triggerEvent() {} })

  assert.match(modal.content, /位置权限/)
  assert.equal(opened, true)
  global.Component = originalComponent
  global.wx = originalWx
})
