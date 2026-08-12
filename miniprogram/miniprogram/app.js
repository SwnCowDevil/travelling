const { createApiClient } = require('./services/api')
const { login } = require('./services/auth')
const { getRuntimeConfig } = require('./config/runtime')

App({
  globalData: {
    apiBaseUrl: '',
    useDevAuth: false,
    api: null,
    authReady: null
  },
  onLaunch() {
    const runtimeConfig = getRuntimeConfig(wx)
    this.globalData.apiBaseUrl = runtimeConfig.apiBaseUrl
    this.globalData.useDevAuth = runtimeConfig.useDevAuth
    this.globalData.api = createApiClient(wx, runtimeConfig.apiBaseUrl)
    this.ensureAuthenticated()
  },
  ensureAuthenticated() {
    const attempt = login(wx, this.globalData.api, { useDevAuth: this.globalData.useDevAuth })
      .then(() => true)
      .catch(() => {
        wx.showToast({ title: this.globalData.useDevAuth ? '本地登录失败' : '微信登录失败', icon: 'none' })
        return false
      })
    this.globalData.authReady = attempt
    return attempt
  }
})
