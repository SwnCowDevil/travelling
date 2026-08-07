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

function saveOrigin(wxApi, origin) {
  wxApi.setStorageSync(ORIGIN_KEY, origin)
  return origin
}

async function resolveSelectedOrigin(api, selected) {
  const fallback = {
    type: 'manual',
    name: manualOriginName(selected.name, selected.address, selected.latitude, selected.longitude),
    regionName: '',
    address: String(selected.address || '').trim(),
    latitude: selected.latitude,
    longitude: selected.longitude,
    source: 'wechat'
  }
  try {
    const latitude = encodeURIComponent(selected.latitude)
    const longitude = encodeURIComponent(selected.longitude)
    const result = await api.request({
      path: `/locations/reverse-geocode?latitude=${latitude}&longitude=${longitude}`
    })
    return {
      type: 'manual',
      name: String(result.name || '').trim() || fallback.name,
      regionName: String(result.region_name || '').trim(),
      address: String(result.address || '').trim(),
      latitude: result.latitude,
      longitude: result.longitude,
      source: result.source || 'amap'
    }
  } catch (_error) {
    return fallback
  }
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
              address: String(address || '').trim(),
              latitude,
              longitude
            }
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

module.exports = {
  ORIGIN_KEY,
  classifyLocationFailure,
  manualOriginName,
  resolveSelectedOrigin,
  saveOrigin,
  createLocationService
}
