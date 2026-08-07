const test = require('node:test')
const assert = require('node:assert/strict')

const { TOKEN_KEY } = require('../../miniprogram/services/api')
const { login } = require('../../miniprogram/services/auth')

test('local development login does not require a WeChat code', async () => {
  let path
  let stored
  const wx = {
    login: () => { throw new Error('wx.login should not run') },
    setStorageSync: (key, value) => { stored = [key, value] }
  }
  const api = { request: async options => { path = options.path; return { access_token: 'dev-token' } } }

  await login(wx, api, { useDevAuth: true })

  assert.equal(path, '/auth/dev')
  assert.deepEqual(stored, [TOKEN_KEY, 'dev-token'])
})
