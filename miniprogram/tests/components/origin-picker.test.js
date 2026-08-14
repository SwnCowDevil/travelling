const test = require('node:test')
const assert = require('node:assert/strict')

test('successful manual selection updates the visible value before emitting', async () => {
  let definition
  let visible
  let emitted
  const originalComponent = global.Component
  const originalWx = global.wx
  global.Component = value => { definition = value }
  global.wx = {
    chooseLocation: options => options.success({ name: '西湖', address: '杭州市', latitude: 30.2, longitude: 120.1 }),
    setStorageSync() {}
  }
  delete require.cache[require.resolve('../../miniprogram/components/origin-picker/index')]
  require('../../miniprogram/components/origin-picker/index')

  await definition.methods.choose.call({
    setData: value => { visible = value.value },
    triggerEvent: (name, detail) => { emitted = [name, detail] }
  })

  assert.equal(visible.name, '西湖')
  assert.deepEqual(emitted, ['change', visible])
  global.Component = originalComponent
  global.wx = originalWx
})

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

test('privacy denial explains the retry without opening system settings', async () => {
  let definition
  let toast
  let opened = false
  let event
  const originalComponent = global.Component
  const originalWx = global.wx
  global.Component = value => { definition = value }
  global.wx = {
    getPrivacySetting: options => options.success({ needAuthorization: true }),
    requirePrivacyAuthorize: options => options.fail({ errMsg: 'privacy deny' }),
    chooseLocation: () => { throw new Error('must not call chooseLocation') },
    showToast: options => { toast = options },
    showModal() { throw new Error('must not show permission modal') },
    openSetting: () => { opened = true }
  }
  delete require.cache[require.resolve('../../miniprogram/components/origin-picker/index')]
  require('../../miniprogram/components/origin-picker/index')

  await definition.methods.choose.call({ triggerEvent: name => { event = name } })

  assert.match(toast.title, /隐私保护/)
  assert.equal(opened, false)
  assert.equal(event, 'cancel')
  global.Component = originalComponent
  global.wx = originalWx
})
