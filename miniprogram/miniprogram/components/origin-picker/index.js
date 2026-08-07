const { classifyLocationFailure, createLocationService } = require('../../services/location')

Component({
  properties: { value: Object },
  methods: {
    async choose() {
      const service = createLocationService(wx)
      try {
        const origin = await service.chooseManualOrigin()
        this.setData({ value: origin })
        this.triggerEvent('change', origin)
      } catch (error) {
        const reason = classifyLocationFailure(error)
        if (reason === 'cancel') {
          this.triggerEvent('cancel')
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
          this.triggerEvent('cancel')
          return
        }
        wx.showToast({ title: '暂时无法选择地点', icon: 'none' })
        this.triggerEvent('cancel')
      }
    }
  }
})
