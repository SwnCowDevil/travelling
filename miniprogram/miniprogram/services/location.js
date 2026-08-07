const ORIGIN_KEY = 'travel_recent_origin'

function classifyLocationFailure(error = {}) {
  const message = String(error.errMsg || error.message || '').toLowerCase()
  if (message.includes('cancel')) return 'cancel'
  if (message.includes('auth deny') || message.includes('authorize') || message.includes('permission')) return 'permission'
  return 'unavailable'
}

function manualOriginName(name, address, latitude, longitude) {
  const provided = String(name || '').trim() || String(address || '').trim()
  if (provided) return provided
  const lat = Number(latitude).toFixed(4)
  const lng = Number(longitude).toFixed(4)
  return `地图选点 ${lat}, ${lng}`
}

function createLocationService(wxApi) {
  return {
    resolveOrigin() {
      return new Promise(resolve => {
        wxApi.getLocation({
          type: 'gcj02',
          success: ({ latitude, longitude }) => resolve({
            type: 'gps', name: '当前位置', latitude, longitude
          }),
          fail: () => {
            const saved = wxApi.getStorageSync(ORIGIN_KEY)
            if (!saved) {
              resolve({ type: 'manual_required' })
              return
            }
            const repaired = {
              ...saved,
              name: manualOriginName(saved.name, saved.address, saved.latitude, saved.longitude)
            }
            if (repaired.name !== saved.name && wxApi.setStorageSync) {
              wxApi.setStorageSync(ORIGIN_KEY, repaired)
            }
            resolve(repaired)
          }
        })
      })
    },
    chooseManualOrigin() {
      return new Promise((resolve, reject) => {
        wxApi.chooseLocation({
          success: ({ name, address, latitude, longitude }) => {
            const origin = {
              type: 'manual',
              name: manualOriginName(name, address, latitude, longitude),
              latitude,
              longitude
            }
            wxApi.setStorageSync(ORIGIN_KEY, origin)
            resolve(origin)
          },
          fail: reject
        })
      })
    },
    requestLocationPermission() {
      return new Promise(resolve => {
        wxApi.openSetting({
          success: result => resolve(Boolean(result.authSetting && result.authSetting['scope.userLocation'])),
          fail: () => resolve(false)
        })
      })
    }
  }
}

module.exports = { ORIGIN_KEY, classifyLocationFailure, manualOriginName, createLocationService }
