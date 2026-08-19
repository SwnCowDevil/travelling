const loadingStages = ['正在筛选适合月份', '正在计算距离与偏好', '正在整理推荐理由']

const FILTER_GROUPS = {
  season: ['旺季', '淡季'],
  crowd: ['人少', '人多'],
  preferences: ['人文', '景色'],
  categories: ['海岛', '古城', '山川', '草原', '城市', '沙漠']
}

const DISTANCE_RANGES = [
  { value: null, label: '不限' },
  { value: 'under-100', label: '<100km', min: 0, max: 100 },
  { value: '100-200', label: '100–200km', min: 100, max: 200 },
  { value: '200-300', label: '200–300km', min: 200, max: 300 },
  { value: '300-400', label: '300–400km', min: 300, max: 400 },
  { value: '400-500', label: '400–500km', min: 400, max: 500 },
  { value: 'over-500', label: '>500km', min: 500 }
]

const DAY_OPTIONS = [1, 2, 3, 5, 7]

function defaultFilters(now = new Date()) {
  return {
    month: now.getMonth() + 1,
    distanceRange: null,
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

function setDays(filters, value) {
  const days = Number(value)
  return { ...filters, days: filters.days === days ? null : days }
}

function setDistanceRange(filters, value) {
  return { ...filters, distanceRange: value || null }
}

function resetOptionalFilters(filters) {
  return {
    ...filters,
    distanceRange: null,
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
  if (filters.days) items.push({ key: 'days', value: filters.days, label: `${filters.days}天` })
  ;['seasons', 'crowd', 'preferences', 'categories', 'transport'].forEach(key => {
    const values = Array.isArray(filters[key]) ? filters[key] : []
    values.forEach(value => items.push({ key, value, label: value }))
  })
  const distance = DISTANCE_RANGES.find(item => item.value === filters.distanceRange)
  if (distance && distance.value) items.push({ key: 'distanceRange', value: distance.value, label: distance.label })
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
    categories: make('categories', FILTER_GROUPS.categories),
    days: DAY_OPTIONS.map(value => ({ value, selected: value === filters.days })),
    distance: DISTANCE_RANGES.map(item => ({
      ...item,
      selected: item.value === (filters.distanceRange || null)
    }))
  }
}

function buildRequest(filters, origin) {
  const crowds = Array.isArray(filters.crowd) ? filters.crowd : (filters.crowd ? [filters.crowd] : [])
  const categories = [...new Set([...(filters.preferences || []), ...(filters.categories || [])])]
  const coordinateLabel = `地图选点 ${Number(origin.latitude).toFixed(4)}, ${Number(origin.longitude).toFixed(4)}`
  const originName = [origin.name, origin.address, origin.regionName]
    .map(value => String(value || '').trim())
    .find(Boolean) || coordinateLabel
  const value = {
    origin_latitude: origin.latitude,
    origin_longitude: origin.longitude,
    origin_name: originName,
    month: filters.month,
    preferred_categories: categories,
    preferred_seasons: filters.seasons || [],
    preferred_crowds: crowds,
    preferred_transport: filters.transport || [],
    sort_mode: 'recommended'
  }
  if (filters.maxDistanceKm) value.max_distance_km = filters.maxDistanceKm
  const distance = DISTANCE_RANGES.find(item => item.value === filters.distanceRange)
  if (distance && distance.value) {
    if (distance.min !== undefined) value.min_distance_km = distance.min
    if (distance.max !== undefined) value.max_distance_km = distance.max
  }
  if (filters.maxBudget) value.max_budget = filters.maxBudget
  if (filters.days) value.available_days = filters.days
  return value
}

module.exports = {
  FILTER_GROUPS,
  DISTANCE_RANGES,
  DAY_OPTIONS,
  loadingStages,
  defaultFilters,
  toggleFilter,
  setMonth,
  setDays,
  setDistanceRange,
  resetOptionalFilters,
  filterSummary,
  filterOptions,
  buildRequest
}
