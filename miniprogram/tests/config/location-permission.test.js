const test = require('node:test')
const assert = require('node:assert/strict')

const app = require('../../miniprogram/app.json')

test('app declares both location private APIs', () => {
  assert.match(app.permission['scope.userLocation'].desc, /距离|出发地/)
  assert.deepEqual(new Set(app.requiredPrivateInfos), new Set(['getLocation', 'chooseLocation']))
  assert.equal(app.__usePrivacyCheck__, true)
})
