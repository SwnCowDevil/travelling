const test = require('node:test')
const assert = require('node:assert/strict')
const { nextParent, filterItems, mapColor, projectMapItems, hitRegion, visibleMapItems } = require('../../miniprogram/pages/map/model')

test('map supports hierarchy drill down and four status filters', () => {
  assert.equal(nextParent({ region_code: '510000' }), '510000')
  const items = [
    { region_code: '510000', direct_status: 'avoid', status_counts: { revisit: 1 } },
    { region_code: '330000', direct_status: null, status_counts: { want: 2 } }
  ]
  assert.deepEqual(filterItems(items, 'revisit').map(item => item.region_code), ['510000'])
  assert.equal(filterItems(items, null).length, 2)
})

test('list data remains usable when visual map is unavailable', () => {
  const items = [{ region_code: '510000', name: '四川', visit_count: 2 }]
  assert.equal(filterItems(items, null)[0].visit_count, 2)
})

test('map model colors, projects, filters, and finds a touched region', () => {
  assert.equal(mapColor({ map_status: 'visited' }), '#20d8cf')
  assert.equal(mapColor({ map_status: 'avoid' }), '#1b3440')
  const items = [{
    region_code: '510000', map_status: 'visited', status_counts: { visited: 1 },
    polygons: [[[100, 30], [110, 30], [100, 40]]]
  }]
  const projected = projectMapItems(items, 300, 200, 16)
  assert.equal(projected[0].paths[0].length, 3)
  const path = projected[0].paths[0]
  const point = path.reduce((result, item) => ({ x: result.x + item.x / 3, y: result.y + item.y / 3 }), { x: 0, y: 0 })
  assert.equal(hitRegion(projected, point.x, point.y).region_code, '510000')
  assert.equal(visibleMapItems(items, 'visited').length, 1)
  assert.equal(visibleMapItems([{ ...items[0], polygons: [] }], null).length, 0)
})
