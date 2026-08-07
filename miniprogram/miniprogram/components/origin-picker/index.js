const { createLocationService } = require('../../services/location')

Component({
  properties: { value: Object },
  methods: {
    async choose() {
      try {
        const origin = await createLocationService(wx).chooseManualOrigin()
        this.triggerEvent('change', origin)
      } catch (_) {
        wx.showToast({ title: '未选择出发地', icon: 'none' })
      }
    }
  }
})
