const ORIGIN_KEY = 'travel_recent_origin'

function createLocationService(wxApi) {
  return {
    resolveOrigin() {
      return new Promise(resolve => {
        wxApi.getLocation({
          type: 'gcj02',
          success: ({ latitude, longitude }) => resolve({
            type: 'gps', name: '当前位置', latitude, longitude
          }),
          fail: () => resolve(wxApi.getStorageSync(ORIGIN_KEY) || { type: 'manual_required' })
        })
      })
    },
    chooseManualOrigin() {
      return new Promise((resolve, reject) => {
        wxApi.chooseLocation({
          success: ({ name, address, latitude, longitude }) => {
            const origin = { type: 'manual', name: name || address, latitude, longitude }
            wxApi.setStorageSync(ORIGIN_KEY, origin)
            resolve(origin)
          },
          fail: reject
        })
      })
    }
  }
}

module.exports = { ORIGIN_KEY, createLocationService }
