const { createLocationService } = require('../../services/location')
const { defaultFilters, buildRequest, loadingStages } = require('./model')
Page({
  data:{ origin:{}, filters:defaultFilters(), loading:false, stage:'', items:[], sessionId:null, fallback:false, showMore:false, pendingRecommend:false },
  async onLoad(){ const origin=await createLocationService(wx).resolveOrigin(); this.setData({origin}) },
  async onOrigin({detail}){
    const shouldRecommend=this.data.pendingRecommend
    this.setData({origin:detail,pendingRecommend:false})
    if(shouldRecommend) await this.recommend()
  },
  async recommend(){
    if(!this.data.origin.latitude){
      this.setData({pendingRecommend:true})
      wx.showToast({title:'请先选择出发地',icon:'none'})
      const picker=this.selectComponent('#origin')
      if(picker) picker.choose()
      return
    }
    this.setData({loading:true,stage:loadingStages[0],items:[]})
    const timers=loadingStages.slice(1).map((stage,i)=>setTimeout(()=>this.setData({stage}),500*(i+1)))
    try {
      const app=getApp()
      const authenticated=await app.globalData.authReady
      if(authenticated===false) throw new Error('本地登录失败')
      const data=await app.globalData.api.request({method:'POST',path:'/recommendations',data:buildRequest(this.data.filters,this.data.origin)})
      this.setData({items:data.items,sessionId:data.session_id,fallback:data.source==='rules'})
    } catch (error) {
      wx.showToast({title:error.message||'推荐请求失败',icon:'none'})
    }
    finally {timers.forEach(clearTimeout);this.setData({loading:false})}
  },
  async next(){const data=await getApp().globalData.api.request({method:'POST',path:`/recommendations/${this.data.sessionId}/next`});this.setData({items:data.items,fallback:data.source==='rules'})},
  toggleMore(){this.setData({showMore:!this.data.showMore})},
  openDetail(e){wx.navigateTo({url:`/pages/destination-detail/index?id=${e.detail.id}`})}
})
