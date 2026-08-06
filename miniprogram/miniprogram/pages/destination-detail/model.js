function weatherLabel(v){return v.kind==='forecast'?'实时预报':v.kind==='climate_reference'?'历史气候参考':'本地气候参考'}
function canSetRevisit(count){return count>0}
module.exports={weatherLabel,canSetRevisit}
