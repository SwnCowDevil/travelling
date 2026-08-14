function weatherLabel(v={}){return v.kind==='forecast'?'实时预报':v.kind==='climate_reference'?'历史气候参考':'本地气候参考'}
function canSetRevisit(count){return count>0}
function text(v,fallback='暂无'){const value=String(v||'').trim();return value||fallback}
function budget(d){if(d.min_budget&&d.max_budget)return `¥${d.min_budget}–${d.max_budget}`;return '预算待估'}
function season(months=[]){return months.length?months.map(v=>`${v}月`).join('、'):'四季皆宜'}
function buildDetailView(destination={},weather={},guide={},context={}){
  const payload=guide.payload||{}
  const isAIGenerated=guide.source==='ai'
  return {
    id:destination.id||0,name:text(destination.name,'目的地'),summary:text(destination.summary,'发现值得前往的风景'),
    emoji:'🏞️',bestSeason:season(destination.suitable_months),daysText:`${Number(context.days)||2}天`,budgetText:budget(destination),ratingText:`${'★'.repeat(Math.max(1,Math.round((Number(destination.quality_score)||.8)*5)))}`,
    isAIGenerated,guideSourceLabel:isAIGenerated?'AI 生成':'规则参考',sourceNotice:isAIGenerated?'AI 生成内容｜景区开放、票价、交通和天气请以官方信息为准':'规则参考内容｜AI 未参与',weatherLabel:weatherLabel(weather),
    weatherDays:(weather.daily||[]).map(v=>({date:text(v.date),temperature:`${v.temperature_min??'--'}–${v.temperature_max??'--'}℃`,rain:`降雨 ${v.precipitation_probability??'--'}%`})),
    transport:(payload.transport||[]).map(v=>text(v)),weatherNotes:(payload.weather||[]).map(v=>text(v)),packing:(payload.packing||[]).map(v=>text(v)),cautions:(payload.cautions||[]).map(v=>text(v)),highlights:(payload.highlights||[]).map(v=>text(v)),
    foods:(payload.foods||[]).map(v=>({name:text(v.name),description:text(v.description),area:text(v.area),averagePrice:text(v.average_price,'价格以现场为准')})),
    itinerary:(payload.itinerary||[]).map(v=>({day:Number(v.day)||1,theme:text(v.theme),morning:text(v.morning),afternoon:text(v.afternoon),evening:text(v.evening),transport:text(v.transport),caution:text(v.caution)}))
  }
}
module.exports={weatherLabel,canSetRevisit,buildDetailView}
