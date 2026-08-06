const { createLocationService } = require('../../services/location')

Component({
  properties: { value: Object },
  methods: {
    async choose() {
      try {
        const origin = await createLocationService(wx).chooseManualOrigin()
        this.triggerEvent('change', origin)
      } catch (_) {}
    }
  }
})
