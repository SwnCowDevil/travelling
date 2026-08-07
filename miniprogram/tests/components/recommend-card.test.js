const test = require('node:test')
const assert = require('node:assert/strict')

test('card view never renders undefined for missing guide fields', () => {
  const { toCardView } = require('../../miniprogram/components/recommend-card/model')
  const view = toCardView({ destination_id: 7, code: 'x', name: '桂林', score: 0.87, distance_km: 128.4 })
  assert.equal(view.destinationId, 7)
  assert.equal(view.transport, '查看详情')
  assert.equal(view.weather, '暂无天气数据')
  assert.equal(view.note, '出发前查看当地提示')
  assert.equal(view.ratingText, '★★★★☆')
  assert.ok(!JSON.stringify(view).includes('undefined'))
})

test('status buttons emit a status event without opening the card', () => {
  let definition
  const originalComponent = global.Component
  global.Component = value => { definition = value }
  delete require.cache[require.resolve('../../miniprogram/components/recommend-card/index')]
  require('../../miniprogram/components/recommend-card/index')

  const events = []
  const context = {
    data: { view: { destinationId: 9 } },
    triggerEvent: (name, detail) => events.push([name, detail])
  }
  definition.methods.setStatus.call(context, { currentTarget: { dataset: { status: 'want' } } })

  assert.deepEqual(events, [['status', { destinationId: 9, status: 'want' }]])
  global.Component = originalComponent
})
