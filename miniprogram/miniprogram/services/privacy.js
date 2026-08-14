function requestPrivacyAuthorization(wxApi) {
  return new Promise(resolve => {
    if (typeof wxApi.requirePrivacyAuthorize !== 'function') {
      resolve(false)
      return
    }
    try {
      wxApi.requirePrivacyAuthorize({
        success: () => resolve(true),
        fail: () => resolve(false)
      })
    } catch (_error) {
      resolve(false)
    }
  })
}

function ensurePrivacyAuthorized(wxApi = {}) {
  const hasSettingApi = typeof wxApi.getPrivacySetting === 'function'
  const hasAuthorizeApi = typeof wxApi.requirePrivacyAuthorize === 'function'
  if (!hasSettingApi && !hasAuthorizeApi) return Promise.resolve(true)
  if (!hasSettingApi) return requestPrivacyAuthorization(wxApi)

  return new Promise(resolve => {
    try {
      wxApi.getPrivacySetting({
        success: result => {
          if (!result.needAuthorization) {
            resolve(true)
            return
          }
          requestPrivacyAuthorization(wxApi).then(resolve)
        },
        fail: () => resolve(false)
      })
    } catch (_error) {
      resolve(false)
    }
  })
}

module.exports = { ensurePrivacyAuthorized }
