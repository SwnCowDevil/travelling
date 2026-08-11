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
  for (const marker of ['custom-guide-card', 'quick-recommend-card', '不知道去哪？试试一键推荐', '正在推荐']) {
    assert.match(wxml, new RegExp(marker))
  }
  assert.doesNotMatch(wxml, /正在为你推荐/)
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

test('recommend entry cards share a white card treatment and compact loading state', () => {
  const config = JSON.parse(fs.readFileSync(path.join(pageDir, 'index.json'), 'utf8'))
  const wxml = fs.readFileSync(path.join(pageDir, 'index.wxml'), 'utf8')
  const wxss = fs.readFileSync(path.join(pageDir, 'index.wxss'), 'utf8')
  assert.equal(config.usingComponents['loading-stage'], '/components/loading-stage/index')
  assert.match(wxml, /<loading-stage wx:if="\{\{loading\}\}" text="\{\{stage\}\}"\/>/)
  assert.match(wxml, /loading="\{\{searchingCustom\}\}"/)
  assert.match(wxss, /\.custom-guide-card,\.quick-recommend-card\{[^}]*background:#fff/)
  assert.match(wxss, /\.custom-guide-card,\.quick-recommend-card\{[^}]*border-radius:/)
  assert.match(wxss, /\.custom-guide-card,\.quick-recommend-card\{[^}]*box-shadow/)
  assert.match(wxss, /\.recommend-cta\.loading\{[^}]*letter-spacing:0/)
})

test('recommend more panel exposes the fixed distance range controls', () => {
  const wxml = fs.readFileSync(path.join(pageDir, 'index.wxml'), 'utf8')
  assert.match(wxml, /距离所在地区/)
  assert.match(wxml, /wx:for="\{\{filterOptions\.distance\}\}"/)
  assert.match(wxml, /data-value="\{\{item\.value\}\}" bindtap="selectDistanceRange"/)
  assert.match(wxml, /filters\.distanceRange/)
})
