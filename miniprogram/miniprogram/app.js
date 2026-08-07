const { createApiClient } = require('./services/api')
const { login } = require('./services/auth')
const localConfig = require('./config/local')

App({
  globalData: {
    apiBaseUrl: localConfig.apiBaseUrl,
    api: null,
    authReady: null
  },
  onLaunch() {
    this.globalData.api = createApiClient(wx, this.globalData.apiBaseUrl)
    this.globalData.authReady = login(wx, this.globalData.api, { useDevAuth: localConfig.useDevAuth })
      .then(() => true)
      .catch(() => {
        wx.showToast({ title: '本地登录失败', icon: 'none' })
        return false
      })
  }
})
