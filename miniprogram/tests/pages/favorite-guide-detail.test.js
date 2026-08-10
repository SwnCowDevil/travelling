const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const path=require('node:path')
const dir=path.join(__dirname,'../../miniprogram/pages/favorite-guide-detail')
test('favorite detail exposes edit save and delete controls',()=>{const w=fs.readFileSync(path.join(dir,'index.wxml'),'utf8');for(const text of ['编辑攻略','保存修改','删除收藏','当地美食','按天攻略'])assert.match(w,new RegExp(text));assert.match(w,/bindtap="save"/)})
