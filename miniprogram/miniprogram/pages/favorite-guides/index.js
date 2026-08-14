const {favoriteSourceLabel}=require('../../utils/guide-source')
Page({
  data:{items:[],loading:true,error:''},
  async onShow(){
    this.setData({loading:true,error:''})
    try{const value=await getApp().globalData.api.request({path:'/favorite-guides'});this.setData({items:(value.items||[]).map(item=>({...item,sourceLabel:favoriteSourceLabel(item.source,item.user_edited)}))})}
    catch(error){this.setData({error:error.message||'收藏攻略加载失败'})}
    finally{this.setData({loading:false})}
  },
  openFavorite(event){wx.navigateTo({url:`/pages/favorite-guide-detail/index?id=${event.currentTarget.dataset.id}`})}
})
