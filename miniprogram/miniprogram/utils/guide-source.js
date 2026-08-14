function favoriteSourceLabel(source, userEdited) {
  if (source === 'ai') return userEdited ? 'AI 生成 · 已编辑' : 'AI 生成'
  if (source === 'rules') return '规则参考'
  return '历史收藏 · 来源未标记'
}

module.exports = { favoriteSourceLabel }
