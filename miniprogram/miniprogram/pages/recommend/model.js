const loadingStages = ['正在筛选适合月份', '正在计算距离与偏好', '正在整理推荐理由']
function defaultFilters(now = new Date()) { return { month: now.getMonth()+1, maxDistanceKm:null, maxBudget:null, days:null, categories:[], seasons:[], crowd:null, transport:[] } }
function buildRequest(f, origin) {
  const value = { origin_latitude:origin.latitude, origin_longitude:origin.longitude, origin_name:origin.name, month:f.month, preferred_categories:f.categories||[], preferred_seasons:f.seasons||[], preferred_crowds:f.crowd?[f.crowd]:[], preferred_transport:f.transport||[] }
  if (f.maxDistanceKm) value.max_distance_km=f.maxDistanceKm
  if (f.maxBudget) value.max_budget=f.maxBudget
  if (f.days) value.available_days=f.days
  return value
}
module.exports={loadingStages,defaultFilters,buildRequest}
