const test = require('node:test')
const assert = require('node:assert/strict')
const { resolveRuntimeConfig, getRuntimeConfig } = require('../../miniprogram/config/runtime')

test('develop uses the production API and real WeChat authentication', () => {
  assert.deepEqual(resolveRuntimeConfig('develop'), {
    apiBaseUrl: 'https://api.sunks.cc',
    useDevAuth: false
  })
})

test('trial and release use the production API and real authentication', () => {
  for (const envVersion of ['trial', 'release']) {
    assert.deepEqual(resolveRuntimeConfig(envVersion), {
      apiBaseUrl: 'https://api.sunks.cc',
      useDevAuth: false
    })
  }
})

test('missing, unknown, and unreadable environments safely use production', () => {
  assert.equal(resolveRuntimeConfig().apiBaseUrl, 'https://api.sunks.cc')
  assert.equal(resolveRuntimeConfig('unknown').useDevAuth, false)
  assert.equal(getRuntimeConfig({ getAccountInfoSync() { throw new Error('unavailable') } }).useDevAuth, false)
})

test('runtime configuration exposes no credential fields', () => {
  const keys = Object.keys(resolveRuntimeConfig('release')).join(' ').toLowerCase()
  assert.doesNotMatch(keys, /token|secret|api.?key/)
})
