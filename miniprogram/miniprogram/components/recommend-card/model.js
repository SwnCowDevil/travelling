const visuals = [
  { emoji: '🏞️', gradient: 'linear-gradient(135deg,#2bb0ff,#1bb28a)' },
  { emoji: '⛰️', gradient: 'linear-gradient(135deg,#56ccf2,#2f80ed)' },
  { emoji: '🏯', gradient: 'linear-gradient(135deg,#f2994a,#eb5757)' },
  { emoji: '🌊', gradient: 'linear-gradient(135deg,#36d1dc,#1bb28a)' },
  { emoji: '🌿', gradient: 'linear-gradient(135deg,#7ed957,#1bb28a)' }
]

function stableIndex(value) {
  return String(value || '').split('').reduce((total, character) => total + character.charCodeAt(0), 0) % visuals.length
}

function ratingText(score) {
  const normalized = Math.max(0, Math.min(1, Number(score) || 0))
  const filled = Math.max(1, Math.round(normalized * 5))
  return `${'★'.repeat(filled)}${'☆'.repeat(5 - filled)}`
}

function toCardView(item = {}) {
  const visual = visuals[stableIndex(item.code || item.name)]
  const distance = Number(item.distance_km)
  const distanceText = Number.isFinite(distance) ? `约 ${distance.toFixed(distance < 100 ? 1 : 0)} km` : '距离待计算'
  return {
    destinationId: item.destination_id || 0,
    code: item.code || '',
    name: item.name || '未知目的地',
    summary: item.summary || '查看目的地详细攻略',
    emoji: visual.emoji,
    gradient: visual.gradient,
    ratingText: ratingText(item.score),
    scoreText: `${Math.round((Number(item.score) || 0) * 100)} 分`,
    tags: [{ label: '当月适合', warning: false }, { label: distanceText, warning: false }],
    badge: Number(item.score) >= 0.85 ? '最推荐' : '',
    transport: item.transport || '查看详情',
    weather: item.weather || '暂无天气数据',
    note: item.reason || item.note || '出发前查看当地提示',
    distanceText,
    selectedStatus: item.selectedStatus || ''
  }
}

module.exports = { ratingText, toCardView }
