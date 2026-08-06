const test = require('node:test')
const assert = require('node:assert/strict')

const config = require('../../miniprogram/config/local')

test('local config points to loopback API without secrets', () => {
  assert.equal(config.apiBaseUrl, 'http://127.0.0.1:8000')
  const keys = Object.keys(config).join(' ').toLowerCase()
  assert.doesNotMatch(keys, /token|secret|api.?key/)
})
