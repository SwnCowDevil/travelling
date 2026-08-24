const DEVELOP_CONFIG = Object.freeze({
  apiBaseUrl: 'https://api.sunks.cc',
  useDevAuth: false
})

const PRODUCTION_CONFIG = Object.freeze({
  apiBaseUrl: 'https://api.sunks.cc',
  useDevAuth: false
})

function resolveRuntimeConfig(envVersion) {
  const selected = envVersion === 'trial' || envVersion === 'release'
    ? PRODUCTION_CONFIG
    : DEVELOP_CONFIG
  return { ...selected }
}

function getRuntimeConfig(wxApi) {
  try {
    const account = wxApi && typeof wxApi.getAccountInfoSync === 'function'
      ? wxApi.getAccountInfoSync()
      : null
    return resolveRuntimeConfig(account && account.miniProgram && account.miniProgram.envVersion)
  } catch (_) {
    return resolveRuntimeConfig('develop')
  }
}

module.exports = { resolveRuntimeConfig, getRuntimeConfig }
