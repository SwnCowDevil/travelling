const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')

const pageDir = path.resolve(__dirname, '../../miniprogram/pages/recommend')

test('recommend page contains the complete v4 structure', () => {
  const wxml = fs.readFileSync(path.join(pageDir, 'index.wxml'), 'utf8')
  const markers = [
    'recommend-hero', 'filter-month', 'filter-season', 'filter-crowd',
    'filter-pref', 'filter-more', 'filter-summary', 'recommend-cta',
    'recommend-results'
  ]
  for (const marker of markers) assert.match(wxml, new RegExp(marker))
  assert.match(wxml, /旅行推荐/)
  assert.match(wxml, /正在为你推荐/)
  assert.match(wxml, /bindtap="chooseOrigin"/)
  assert.match(wxml, /origin\.name/)
  assert.match(wxml, /正在识别地点/)
  assert.match(wxml, /AI 未参与，已使用可靠规则推荐/)
  assert.doesNotMatch(wxml, /<origin-picker/)
})

test('recommend page uses v4 color tokens and supported animations', () => {
  const wxss = fs.readFileSync(path.join(pageDir, 'index.wxss'), 'utf8')
  assert.match(wxss, /#1bb28a/i)
  assert.match(wxss, /#ff9f43/i)
  assert.match(wxss, /@keyframes/)
  assert.doesNotMatch(wxss, /prefers-reduced-motion/)
})
