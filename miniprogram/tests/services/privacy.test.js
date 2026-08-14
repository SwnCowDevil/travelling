const test = require('node:test')
const assert = require('node:assert/strict')
const { ensurePrivacyAuthorized } = require('../../miniprogram/services/privacy')

test('older WeChat runtimes without privacy APIs remain compatible', async () => {
  assert.equal(await ensurePrivacyAuthorized({}), true)
})

test('already-authorized privacy state does not request authorization again', async () => {
  let requested = 0
  const wx = {
    getPrivacySetting: options => options.success({ needAuthorization: false }),
    requirePrivacyAuthorize: () => { requested += 1 }
  }
  assert.equal(await ensurePrivacyAuthorized(wx), true)
  assert.equal(requested, 0)
})

test('privacy authorization resolves false when the user declines', async () => {
  const wx = {
    getPrivacySetting: options => options.success({ needAuthorization: true }),
    requirePrivacyAuthorize: options => options.fail({ errMsg: 'requirePrivacyAuthorize:fail privacy deny' })
  }
  assert.equal(await ensurePrivacyAuthorized(wx), false)
})

test('privacy setting failures fail closed', async () => {
  const wx = { getPrivacySetting: options => options.fail({ errMsg: 'system error' }) }
  assert.equal(await ensurePrivacyAuthorized(wx), false)
})
