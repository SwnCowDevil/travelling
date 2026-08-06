const test=require('node:test');const assert=require('node:assert/strict')
const {weatherLabel,canSetRevisit}=require('../../miniprogram/pages/destination-detail/model')
test('weather source labels are explicit',()=>{assert.equal(weatherLabel({kind:'forecast'}),'实时预报');assert.equal(weatherLabel({kind:'climate_reference'}),'历史气候参考');assert.equal(weatherLabel({kind:'local_climate'}),'本地气候参考')})
test('revisit requires a recorded visit',()=>{assert.equal(canSetRevisit(0),false);assert.equal(canSetRevisit(1),true)})
