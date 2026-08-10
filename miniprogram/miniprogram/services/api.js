const TOKEN_KEY = 'travel_access_token'

class ApiError extends Error {
  constructor(message, code, traceId, statusCode) {
    super(message)
    this.code = code
    this.traceId = traceId
    this.statusCode = statusCode
  }
}

function validationErrorMessage(detail) {
  if (!Array.isArray(detail) || !detail.length) return null
  const issue = detail[0] || {}
  const field = Array.isArray(issue.loc) ? issue.loc[issue.loc.length - 1] : ''
  const labels = {
    origin_name: '出发地名称',
    origin_latitude: '出发地纬度',
    origin_longitude: '出发地经度',
    month: '出行月份'
  }
  return `${labels[field] || '请求参数'}不正确，请重新选择`
}

function createApiClient(wxApi, baseUrl) {
  return {
    request({ method = 'GET', path, data, timeout }) {
      return new Promise((resolve, reject) => {
        const token = wxApi.getStorageSync(TOKEN_KEY)
        const header = { 'Content-Type': 'application/json' }
        if (token) header.Authorization = `Bearer ${token}`
        wxApi.request({
          url: `${baseUrl.replace(/\/$/, '')}${path}`,
          method,
          data,
          header,
          ...(timeout ? { timeout } : {}),
          success(response) {
            if (response.statusCode >= 200 && response.statusCode < 300) {
              resolve(response.data)
              return
            }
            if (response.statusCode === 401) {
              wxApi.removeStorageSync(TOKEN_KEY)
              reject(new ApiError('登录已过期', 'UNAUTHORIZED', null, 401))
              return
            }
            const detail = response.data && response.data.detail
            const validationMessage = validationErrorMessage(detail)
            reject(new ApiError(
              validationMessage || (detail && detail.message) || '请求失败',
              (detail && detail.code) || 'REQUEST_FAILED',
              response.data && (response.data.traceId || response.data.trace_id),
              response.statusCode
            ))
          },
          fail(error) {
            reject(new ApiError(error.errMsg || '网络不可用', 'NETWORK_ERROR'))
          }
        })
      })
    }
  }
}

module.exports = { ApiError, TOKEN_KEY, validationErrorMessage, createApiClient }
