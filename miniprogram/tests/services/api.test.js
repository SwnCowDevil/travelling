const test = require('node:test')
const assert = require('node:assert/strict')

const { createApiClient } = require('../../miniprogram/services/api')

test('request carries bearer token', async () => {
  let options
  const wx = {
    getStorageSync: () => 'session-token',
    request: (value) => { options = value; value.success({ statusCode: 200, data: { ok: true } }) }
  }
  const result = await createApiClient(wx, 'https://api.example.com').request({ path: '/health' })
  assert.equal(options.header.Authorization, 'Bearer session-token')
  assert.deepEqual(result, { ok: true })
})

test('401 clears local session', async () => {
  let cleared = false
  const wx = {
    getStorageSync: () => 'expired',
    removeStorageSync: () => { cleared = true },
    request: (value) => value.success({ statusCode: 401, data: {} })
  }
  await assert.rejects(
    createApiClient(wx, 'https://api.example.com').request({ path: '/private' }),
    error => error.code === 'UNAUTHORIZED'
  )
  assert.equal(cleared, true)
})

test('business errors preserve code and traceId', async () => {
  const wx = {
    getStorageSync: () => '',
    request: (value) => value.success({
      statusCode: 409,
      data: { detail: { code: 'DUPLICATE_VISIT_DATE', message: '重复' }, traceId: 'trace-1' }
    })
  }
  await assert.rejects(
    createApiClient(wx, 'https://api.example.com').request({ path: '/visit-records' }),
    error => error.code === 'DUPLICATE_VISIT_DATE' && error.traceId === 'trace-1'
  )
})

test('validation errors expose the invalid field instead of generic failure', async () => {
  const wx = {
    getStorageSync: () => 'token',
    request: value => value.success({
      statusCode: 422,
      data: { detail: [{ type: 'string_too_short', loc: ['body', 'origin_name'], msg: 'String should have at least 1 character' }] }
    })
  }
  await assert.rejects(
    createApiClient(wx, 'https://api.example.com').request({ path: '/recommendations' }),
    error => error.statusCode === 422 && /出发地/.test(error.message)
  )
})
