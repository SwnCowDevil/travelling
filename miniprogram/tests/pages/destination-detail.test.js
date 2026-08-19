const test=require('node:test');const assert=require('node:assert/strict')
const {weatherLabel,canSetRevisit,buildDetailView,normalizeGuideDays}=require('../../miniprogram/pages/destination-detail/model')
test('weather source labels are explicit',()=>{assert.equal(weatherLabel({kind:'forecast'}),'实时预报');assert.equal(weatherLabel({kind:'climate_reference'}),'历史气候参考');assert.equal(weatherLabel({kind:'local_climate'}),'本地气候参考')})
test('revisit requires a recorded visit',()=>{assert.equal(canSetRevisit(0),false);assert.equal(canSetRevisit(1),true)})
test('guide days accept the full custom range and clamp outside it',()=>{assert.equal(normalizeGuideDays('15'),15);assert.equal(normalizeGuideDays('16'),15);assert.equal(normalizeGuideDays('0'),1);assert.equal(normalizeGuideDays('abc'),2)})

test('structured guide renders foods and exact daily itinerary without object strings',()=>{
  const view=buildDetailView(
    {id:7,code:'grassland',name:'锡林郭勒草原',summary:'辽阔草原',suitable_months:[6,7,8],min_budget:1200,max_budget:2600,quality_score:.9},
    {kind:'forecast',daily:[{date:'2026-08-08',temperature_min:15,temperature_max:27,precipitation_probability:20}]},
    {source:'ai',payload:{transport:['飞机转汽车'],weather:['昼夜温差大'],packing:['外套'],cautions:['注意防晒'],highlights:['草原骑马'],foods:[{name:'手把肉',description:'草原风味',area:'锡林浩特',average_price:'约80元/人'}],itinerary:[{day:1,theme:'草原初见',morning:'抵达',afternoon:'骑马',evening:'看星空',transport:'包车',caution:'保暖'}]}},
    {days:1}
  )
  assert.equal(view.foods[0].averagePrice,'约80元/人')
  assert.equal(view.itinerary[0].morning,'抵达')
  assert.equal(view.guideSourceLabel,'AI 生成')
  assert.equal(view.isAIGenerated,true)
  assert.equal(view.sourceNotice,'AI 生成内容｜景区开放、票价、交通和天气请以官方信息为准')
  assert.ok(!JSON.stringify(view).includes('[object Object]'))
})

test('rule guide is never labeled as AI generated',()=>{
  const view=buildDetailView({name:'测试目的地'},{},{source:'rules',payload:{}},{days:2})
  assert.equal(view.guideSourceLabel,'规则参考')
  assert.equal(view.isAIGenerated,false)
  assert.equal(view.sourceNotice,'规则参考内容｜AI 未参与')
})
