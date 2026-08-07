const loadingStages = ['正在筛选适合月份', '正在计算距离与偏好', '正在整理推荐理由']

const FILTER_GROUPS = {
  season: ['旺季', '淡季'],
  crowd: ['人少', '人多'],
  preferences: ['人文', '景色'],
  categories: ['海岛', '古城', '山川', '草原', '城市', '沙漠']
}

function defaultFilters(now = new Date()) {
  return {
    month: now.getMonth() + 1,
    maxDistanceKm: null,
    maxBudget: null,
    days: null,
    categories: [],
    preferences: [],
    seasons: [],
    crowd: [],
    transport: [],
    bestOnly: false
  }
}

function toggleFilter(filters, group, value) {
  const current = Array.isArray(filters[group]) ? filters[group] : []
  const next = current.includes(value)
    ? current.filter(item => item !== value)
    : [...current, value]
  return { ...filters, [group]: next }
}

function setMonth(filters, month) {
  return { ...filters, month: Number(month) }
}

function resetOptionalFilters(filters) {
  return {
    ...filters,
    maxDistanceKm: null,
    maxBudget: null,
    days: null,
    categories: [],
    preferences: [],
    seasons: [],
    crowd: [],
    transport: [],
    bestOnly: false
  }
}

function filterSummary(filters) {
  const items = [{ key: 'month', value: filters.month, label: `${filters.month}月` }]
  ;['seasons', 'crowd', 'preferences', 'categories', 'transport'].forEach(key => {
    const values = Array.isArray(filters[key]) ? filters[key] : []
    values.forEach(value => items.push({ key, value, label: value }))
  })
  if (filters.bestOnly) items.push({ key: 'bestOnly', value: true, label: '最推荐' })
  return items
}

function filterOptions(filters) {
  const make = (group, values) => values.map(value => ({
    value,
    selected: (filters[group] || []).includes(value)
  }))
  return {
    season: make('seasons', FILTER_GROUPS.season),
    crowd: make('crowd', FILTER_GROUPS.crowd),
    preferences: make('preferences', FILTER_GROUPS.preferences),
    categories: make('categories', FILTER_GROUPS.categories)
  }
}

function buildRequest(filters, origin) {
  const crowds = Array.isArray(filters.crowd) ? filters.crowd : (filters.crowd ? [filters.crowd] : [])
  const categories = [...new Set([...(filters.preferences || []), ...(filters.categories || [])])]
  const value = {
    origin_latitude: origin.latitude,
    origin_longitude: origin.longitude,
    origin_name: origin.name,
    month: filters.month,
    preferred_categories: categories,
    preferred_seasons: filters.seasons || [],
    preferred_crowds: crowds,
    preferred_transport: filters.transport || [],
    sort_mode: 'recommended'
  }
  if (filters.maxDistanceKm) value.max_distance_km = filters.maxDistanceKm
  if (filters.maxBudget) value.max_budget = filters.maxBudget
  if (filters.days) value.available_days = filters.days
  return value
}

module.exports = {
  FILTER_GROUPS,
  loadingStages,
  defaultFilters,
  toggleFilter,
  setMonth,
  resetOptionalFilters,
  filterSummary,
  filterOptions,
  buildRequest
}
