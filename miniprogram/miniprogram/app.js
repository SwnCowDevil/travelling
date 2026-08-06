const { createApiClient } = require('./services/api')
const localConfig = require('./config/local')

App({
  globalData: {
    apiBaseUrl: localConfig.apiBaseUrl,
    api: null
  },
  onLaunch() {
    this.globalData.api = createApiClient(wx, this.globalData.apiBaseUrl)
  }
})
