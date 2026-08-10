const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const path=require('node:path')
const dir=path.join(__dirname,'../../miniprogram/pages/favorite-guides')
test('favorite list page presents saved guide cards',()=>{const w=fs.readFileSync(path.join(dir,'index.wxml'),'utf8');assert.match(w,/收藏攻略/);assert.match(w,/wx:for/);assert.match(w,/bindtap="openFavorite"/)})
