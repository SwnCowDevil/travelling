const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')

const pageDir = path.resolve(__dirname, '../../miniprogram/pages/me')

test('profile page contains the complete v4 structure and real menus', () => {
  const wxml = fs.readFileSync(path.join(pageDir, 'index.wxml'), 'utf8')
  for (const marker of ['me-hero', 'me-stats', '去过', '想去', '不想去', '我的旅行地图', '到访记录', 'AI 设置']) {
    assert.match(wxml, new RegExp(marker))
  }
  assert.equal((wxml.match(/待扩展/g) || []).length, 2)
})

test('profile page uses v4 gradient, cards, and motion', () => {
  const wxss = fs.readFileSync(path.join(pageDir, 'index.wxss'), 'utf8')
  assert.match(wxss, /#1bb28a/i)
  assert.match(wxss, /linear-gradient/)
  assert.match(wxss, /@keyframes/)
})

test('profile avatar keeps a non-shrinkable square geometry', () => {
  const wxss = fs.readFileSync(path.join(pageDir, 'index.wxss'), 'utf8')
  assert.match(wxss, /\.avatar\{[^}]*flex:0 0 132rpx/)
  assert.match(wxss, /\.avatar\{[^}]*min-width:132rpx/)
  assert.match(wxss, /\.avatar\{[^}]*min-height:132rpx/)
  assert.match(wxss, /\.avatar\{[^}]*box-sizing:border-box/)
})
