const { TOKEN_KEY } = require('./api')

async function login(wxApi, api, options = {}) {
  if (options.useDevAuth) {
    const session = await api.request({ method: 'POST', path: '/auth/dev' })
    wxApi.setStorageSync(TOKEN_KEY, session.access_token)
    return session
  }
  return new Promise((resolve, reject) => {
    wxApi.login({
      success: async ({ code }) => {
        try {
          const session = await api.request({ method: 'POST', path: '/auth/wechat', data: { code } })
          wxApi.setStorageSync(TOKEN_KEY, session.access_token)
          resolve(session)
        } catch (error) { reject(error) }
      },
      fail: reject
    })
  })
}

module.exports = { login }
