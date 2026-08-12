const test = require('node:test')
const assert = require('node:assert/strict')
const { resolveRuntimeConfig, getRuntimeConfig } = require('../../miniprogram/config/runtime')

test('develop uses the local API and development authentication', () => {
  assert.deepEqual(resolveRuntimeConfig('develop'), {
    apiBaseUrl: 'http://127.0.0.1:8000',
    useDevAuth: true
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

test('missing, unknown, and unreadable environments fall back to develop', () => {
  assert.equal(resolveRuntimeConfig().apiBaseUrl, 'http://127.0.0.1:8000')
  assert.equal(resolveRuntimeConfig('unknown').useDevAuth, true)
  assert.equal(getRuntimeConfig({ getAccountInfoSync() { throw new Error('unavailable') } }).useDevAuth, true)
})

test('runtime configuration exposes no credential fields', () => {
  const keys = Object.keys(resolveRuntimeConfig('release')).join(' ').toLowerCase()
  assert.doesNotMatch(keys, /token|secret|api.?key/)
})
