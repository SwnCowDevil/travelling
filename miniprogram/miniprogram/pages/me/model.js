function toProfileStats(summary = {}, favorites = 0) {
  const stats = (summary.items || []).reduce((stats, item) => {
    const counts = item.status_counts || {}
    stats.visited += Number(counts.visited || 0) + Number(counts.revisit || 0)
    stats.want += Number(counts.want || 0)
    stats.avoid += Number(counts.avoid || 0)
    return stats
  }, { visited: 0, want: 0, avoid: 0 })
  stats.favorites = Number(favorites || 0)
  return stats
}

module.exports = { toProfileStats }
