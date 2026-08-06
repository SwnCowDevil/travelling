const test = require('node:test')
const assert = require('node:assert/strict')
const { nextParent, filterItems } = require('../../miniprogram/pages/map/model')

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
