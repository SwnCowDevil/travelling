function nextParent(item){return item.region_code}
function filterItems(items,status){if(!status)return items;return items.filter(item=>item.direct_status===status||(item.status_counts&&item.status_counts[status]>0))}
module.exports={nextParent,filterItems}
