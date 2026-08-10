const test=require('node:test')
const assert=require('node:assert/strict')
const fs=require('node:fs')
const path=require('node:path')

const dir=path.resolve(__dirname,'../../miniprogram/pages/map')

test('footprint page exposes a default canvas map and map list switch',()=>{
  const wxml=fs.readFileSync(path.join(dir,'index.wxml'),'utf8')
  const wxss=fs.readFileSync(path.join(dir,'index.wxss'),'utf8')
  for(const marker of ['footprint-canvas',"mode === 'map'",'bindtap="toggleMode"','地图','列表','bindtap="tapMap"'])assert.match(wxml,new RegExp(marker))
  assert.match(wxml,/地图数据暂不可用，已切换为列表模式/)
  assert.match(wxss,/\.map-stage\{[^}]*background:#0b1d2b/)
})

test('mode switching keeps the selected hierarchy and filter',()=>{
  let definition
  const originalPage=global.Page
  global.Page=value=>{definition=value}
  delete require.cache[require.resolve('../../miniprogram/pages/map/index')]
  require('../../miniprogram/pages/map/index')
  const page={data:{mode:'map',parentCode:'510000',status:'visited',geometryAvailable:true},setData(value){Object.assign(this.data,value)},drawMap(){},requestMapMode(){this.setData({mode:'map'})}}
  definition.toggleMode.call(page)
  assert.deepEqual(page.data,{mode:'list',parentCode:'510000',status:'visited',geometryAvailable:true})
  definition.toggleMode.call(page)
  assert.equal(page.data.mode,'map')
  global.Page=originalPage
})

test('returning to map mode reinitializes its Canvas node',()=>{
  let definition
  const originalPage=global.Page
  global.Page=value=>{definition=value}
  delete require.cache[require.resolve('../../miniprogram/pages/map/index')]
  require('../../miniprogram/pages/map/index')
  let initializations=0
  const page={
    data:{mode:'list',geometryAvailable:true},
    setData(value,done){Object.assign(this.data,value);if(done)done()},
    initCanvas(){initializations++},requestMapMode(){this.initCanvas();this.setData({mode:'map'})},
    drawMap(){throw new Error('the previous Canvas context must not be reused')},
  }
  definition.toggleMode.call(page)
  assert.equal(page.data.mode,'map')
  assert.equal(initializations,1)
  global.Page=originalPage
})

test('hierarchy title and return action remain available in list mode',()=>{
  const wxml=fs.readFileSync(path.join(dir,'index.wxml'),'utf8')
  assert.ok(wxml.indexOf('class="map-title"') < wxml.indexOf('class="map-mode"'))
  assert.match(wxml,/bindtap="backToCountry"/)
})

test('touching a province drills down but a city remains the final map level',()=>{
  let definition
  const originalPage=global.Page
  global.Page=value=>{definition=value}
  delete require.cache[require.resolve('../../miniprogram/pages/map/index')]
  require('../../miniprogram/pages/map/index')
  const events=[]
  const page={data:{projected:[{region_code:'510000',level:'province',paths:[[{x:0,y:0},{x:30,y:0},{x:0,y:30}]]}]},drill(event){events.push(event.currentTarget.dataset)}}
  definition.tapMap.call(page,{detail:{x:8,y:8}})
  assert.deepEqual(events,[{code:'510000',level:'province'}])
  page.data.projected[0].level='city'
  definition.tapMap.call(page,{detail:{x:8,y:8}})
  assert.equal(events.length,1)
  global.Page=originalPage
})

test('returning to the country map clears only the selected hierarchy',()=>{
  let definition
  const originalPage=global.Page
  global.Page=value=>{definition=value}
  delete require.cache[require.resolve('../../miniprogram/pages/map/index')]
  require('../../miniprogram/pages/map/index')
  let loads=0
  const page={
    data:{parentCode:'510000',status:'visited',mode:'map'},
    setData(value){Object.assign(this.data,value)},
    load(){loads++},
  }
  definition.backToCountry.call(page)
  assert.equal(page.data.parentCode,null)
  assert.equal(page.data.status,'visited')
  assert.equal(page.data.mode,'map')
  assert.equal(loads,1)
  global.Page=originalPage
})
