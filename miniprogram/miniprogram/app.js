const { createApiClient } = require('./services/api')

App({
  globalData: {
    apiBaseUrl: 'https://api.example.com',
    api: null
  },
  onLaunch() {
    this.globalData.api = createApiClient(wx, this.globalData.apiBaseUrl)
  }
})
