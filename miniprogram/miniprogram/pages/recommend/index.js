const {
  classifyLocationFailure,
  createLocationService,
  resolveSelectedOrigin,
  saveOrigin
} = require('../../services/location')
const {
  defaultFilters,
  buildRequest,
  loadingStages,
  toggleFilter,
  setMonth,
  resetOptionalFilters,
  filterSummary,
  filterOptions
} = require('./model')

const months = Array.from({ length: 12 }, (_, index) => index + 1)

Page({
  data: {
    origin: {},
    filters: defaultFilters(),
    months,
    filterOptions: filterOptions(defaultFilters()),
    summaries: filterSummary(defaultFilters()),
    activePanel: '',
    loading: false,
    stage: '',
    items: [],
    sessionId: null,
    hasMore: false,
    fallback: false,
    pendingRecommend: false,
    resolvingOrigin: false
  },

  async onLoad() {
    const version = this._originVersion || 0
    const origin = await createLocationService(wx).resolveOrigin()
    if ((this._originVersion || 0) === version) this.setData({ origin })
  },

  refreshFilterView(filters) {
    this.setData({ filters, filterOptions: filterOptions(filters), summaries: filterSummary(filters) })
  },

  togglePanel(event) {
    const panel = event.currentTarget.dataset.panel
    this.setData({ activePanel: this.data.activePanel === panel ? '' : panel })
  },

  closeFilters() { this.setData({ activePanel: '' }) },

  selectMonth(event) {
    this.refreshFilterView(setMonth(this.data.filters, event.currentTarget.dataset.month))
  },

  toggleOption(event) {
    const { group, value } = event.currentTarget.dataset
    this.refreshFilterView(toggleFilter(this.data.filters, group, value))
  },

  toggleBest() {
    this.refreshFilterView({ ...this.data.filters, bestOnly: !this.data.filters.bestOnly })
  },

  removeSummary(event) {
    const { key, value } = event.currentTarget.dataset
    if (key === 'month') return
    if (key === 'bestOnly') {
      this.refreshFilterView({ ...this.data.filters, bestOnly: false })
      return
    }
    this.refreshFilterView(toggleFilter(this.data.filters, key, value))
  },

  resetFilters() { this.refreshFilterView(resetOptionalFilters(this.data.filters)) },

  async chooseOrigin() {
    const service = createLocationService(wx)
    try {
      const selected = await service.chooseManualOrigin()
      this.setData({ resolvingOrigin: true })
      const app = getApp()
      let authenticated = await app.globalData.authReady
      if (authenticated === false && app.ensureAuthenticated) {
        authenticated = await app.ensureAuthenticated()
      }
      const origin = await resolveSelectedOrigin(app.globalData.api, selected)
      saveOrigin(wx, origin)
      await this.onOrigin({ detail: origin })
    } catch (error) {
      const reason = classifyLocationFailure(error)
      if (reason === 'cancel') {
        this.onOriginCancel()
        return
      }
      if (reason === 'permission') {
        const confirmed = await new Promise(resolve => {
          wx.showModal({
            title: '需要位置权限',
            content: '请在设置中允许使用位置权限，用于选择出发地和计算距离。',
            confirmText: '去设置',
            success: result => resolve(Boolean(result.confirm)),
            fail: () => resolve(false)
          })
        })
        if (confirmed) await service.requestLocationPermission()
        this.onOriginCancel()
        return
      }
      wx.showToast({ title: '暂时无法选择地点', icon: 'none' })
      this.onOriginCancel()
    } finally {
      this.setData({ resolvingOrigin: false })
    }
  },

  async onOrigin({ detail }) {
    this._originVersion = (this._originVersion || 0) + 1
    const shouldRecommend = this.data.pendingRecommend
    this.setData({ origin: detail, pendingRecommend: false })
    if (shouldRecommend) await this.recommend()
  },

  onOriginCancel() { this.setData({ pendingRecommend: false }) },

  async recommend() {
    if (!this.data.origin.latitude) {
      this.setData({ pendingRecommend: true })
      wx.showToast({ title: '请先选择出发地', icon: 'none' })
      await this.chooseOrigin()
      return
    }
    this.closeFilters()
    this.setData({ loading: true, stage: loadingStages[0], items: [] })
    const timers = loadingStages.slice(1).map((stage, index) => (
      setTimeout(() => this.setData({ stage }), 500 * (index + 1))
    ))
    try {
      const app = getApp()
      let authenticated = await app.globalData.authReady
      if (authenticated === false && app.ensureAuthenticated) {
        authenticated = await app.ensureAuthenticated()
      }
      if (authenticated === false) throw new Error('本地登录失败')
      const data = await app.globalData.api.request({
        method: 'POST',
        path: '/recommendations',
        data: buildRequest(this.data.filters, this.data.origin)
      })
      this.setData({
        items: data.items,
        sessionId: data.session_id,
        hasMore: Boolean(data.has_more),
        fallback: data.source === 'rules'
      })
    } catch (error) {
      wx.showToast({ title: error.message || '推荐请求失败', icon: 'none' })
    } finally {
      timers.forEach(clearTimeout)
      this.setData({ loading: false })
    }
  },

  async next() {
    this.setData({ loading: true, stage: '正在换一批推荐' })
    try {
      const data = await getApp().globalData.api.request({
        method: 'POST',
        path: `/recommendations/${this.data.sessionId}/next`
      })
      this.setData({ items: data.items, hasMore: Boolean(data.has_more), fallback: data.source === 'rules' })
    } catch (error) {
      wx.showToast({ title: error.message || '换一批失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  async onCardStatus(event) {
    const { destinationId, status } = event.detail
    try {
      await getApp().globalData.api.request({
        method: 'PUT',
        path: `/destination-statuses/${destinationId}`,
        data: { status }
      })
      const items = this.data.items.map(item => (
        item.destination_id === destinationId ? { ...item, selectedStatus: status } : item
      ))
      this.setData({ items })
      wx.showToast({ title: '已保存' })
    } catch (error) {
      if (error.code === 'REVISIT_REQUIRES_VISIT') {
        wx.showModal({ title: '先补充到访记录', content: '“想再去”需要至少一条到访记录。' })
        return
      }
      wx.showToast({ title: error.message || '保存失败', icon: 'none' })
    }
  },

  openDetail(event) {
    wx.navigateTo({ url: `/pages/destination-detail/index?id=${event.detail.id}` })
  }
})
