const test = require('node:test')
const assert = require('node:assert/strict')
const sitemap = require('../../miniprogram/sitemap.json')

test('sitemap declares at least one valid indexing rule', () => {
  assert.ok(Array.isArray(sitemap.rules))
  assert.ok(sitemap.rules.length > 0)
  assert.deepEqual(sitemap.rules[0], { action: 'allow', page: '*' })
})
