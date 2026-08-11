const test=require('node:test')
const assert=require('node:assert/strict')
const fs=require('node:fs')
const path=require('node:path')

const dir=path.resolve(__dirname,'../../miniprogram/pages/map')

test('footprint page temporarily exposes list-only mode without map download controls',()=>{
  const wxml=fs.readFileSync(path.join(dir,'index.wxml'),'utf8')
  const script=fs.readFileSync(path.join(dir,'index.js'),'utf8')
  assert.doesNotMatch(wxml,/footprint-canvas|bindtap="toggleMode"|正在下载地图包/)
  assert.doesNotMatch(script,/ensureMapPack|initCanvas|drawMap|requestMapMode|tapMap/)
  assert.match(wxml,/旅行足迹/)
  assert.match(wxml,/class="list-mode"/)
})

test('hierarchy title and return action remain available in list mode',()=>{
  const wxml=fs.readFileSync(path.join(dir,'index.wxml'),'utf8')
  assert.ok(wxml.indexOf('class="map-title"') < wxml.indexOf('class="list-mode"'))
  assert.match(wxml,/bindtap="backToCountry"/)
})

test('returning to the country list clears only the selected hierarchy',()=>{
  let definition
  const originalPage=global.Page
  global.Page=value=>{definition=value}
  delete require.cache[require.resolve('../../miniprogram/pages/map/index')]
  require('../../miniprogram/pages/map/index')
  let loads=0
  const page={
    data:{parentCode:'510000',status:'visited'},
    setData(value){Object.assign(this.data,value)},
    load(){loads++},
  }
  definition.backToCountry.call(page)
  assert.equal(page.data.parentCode,null)
  assert.equal(page.data.status,'visited')
  assert.equal(loads,1)
  global.Page=originalPage
})
