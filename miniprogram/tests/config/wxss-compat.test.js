const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')

test('app WXSS avoids unsupported reduced-motion media query', () => {
  const source = fs.readFileSync(
    path.resolve(__dirname, '../../miniprogram/app.wxss'),
    'utf8'
  )
  assert.doesNotMatch(source, /prefers-reduced-motion/)
})
