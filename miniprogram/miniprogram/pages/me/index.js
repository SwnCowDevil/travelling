const { toProfileStats } = require('./model')

Page({
  data: {
    avatar: '',
    name: '微信用户',
    subtitle: '你的个人旅行空间',
    stats: { visited: 0, want: 0, avoid: 0, favorites: 0 },
    loading: false
  },

  async onShow() {
    this.setData({ loading: true })
    try {
      const app = getApp()
      const authenticated = await app.globalData.authReady
      if (authenticated === false) return
      const [summary, favorites] = await Promise.all([
        app.globalData.api.request({ path: '/map/summary' }),
        app.globalData.api.request({ path: '/favorite-guides' })
      ])
      this.setData({ stats: toProfileStats(summary, (favorites.items || []).length) })
    } catch (_) {
      this.setData({ stats: { visited: 0, want: 0, avoid: 0, favorites: 0 } })
    } finally {
      this.setData({ loading: false })
    }
  },

  chooseAvatar(event) { this.setData({ avatar: event.detail.avatarUrl }) },
  openMap() { wx.switchTab({ url: '/pages/map/index' }) },
  openVisits() { wx.navigateTo({ url: '/pages/visit-records/index' }) },
  openFavorites() { wx.navigateTo({ url: '/pages/favorite-guides/index' }) },
  openAI() { wx.navigateTo({ url: '/pages/ai-settings/index' }) },
  showComingSoon() { wx.showToast({ title: '敬请期待', icon: 'none' }) }
})
