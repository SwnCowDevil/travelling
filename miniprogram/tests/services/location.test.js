const test = require('node:test')
const assert = require('node:assert/strict')
const { classifyLocationFailure, createLocationService } = require('../../miniprogram/services/location')

test('location failures distinguish cancellation from permission denial', () => {
  assert.equal(classifyLocationFailure({ errMsg: 'chooseLocation:fail cancel' }), 'cancel')
  assert.equal(classifyLocationFailure({ errMsg: 'getLocation:fail auth deny' }), 'permission')
  assert.equal(classifyLocationFailure({ errMsg: 'chooseLocation:fail system error' }), 'unavailable')
})

test('location permission can be reopened from settings', async () => {
  const wx = { openSetting: options => options.success({ authSetting: { 'scope.userLocation': true } }) }
  const result = await createLocationService(wx).requestLocationPermission()
  assert.equal(result, true)
})

test('location success returns coordinates', async () => {
  const wx = { getLocation: options => options.success({ latitude: 31.2, longitude: 121.4 }) }
  const result = await createLocationService(wx).resolveOrigin()
  assert.deepEqual(result, { type: 'gps', name: '当前位置', latitude: 31.2, longitude: 121.4 })
})

test('location rejection asks for manual origin', async () => {
  const wx = {
    getStorageSync: () => null,
    getLocation: options => options.fail({ errMsg: 'auth deny' })
  }
  const result = await createLocationService(wx).resolveOrigin()
  assert.equal(result.type, 'manual_required')
})

test('recent manual origin can be reused', async () => {
  const saved = { type: 'manual', name: '杭州西湖', latitude: 30.25, longitude: 120.15 }
  const wx = { getStorageSync: () => saved, getLocation: options => options.fail({}) }
  const result = await createLocationService(wx).resolveOrigin()
  assert.deepEqual(result, saved)
})
