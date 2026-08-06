const { createLocationService } = require('../../services/location')
const { defaultFilters, buildRequest, loadingStages } = require('./model')
Page({
  data:{ origin:{}, filters:defaultFilters(), loading:false, stage:'', items:[], sessionId:null, fallback:false, showMore:false },
  async onLoad(){ const origin=await createLocationService(wx).resolveOrigin(); this.setData({origin}) },
  onOrigin({detail}){this.setData({origin:detail})},
  async recommend(){
    if(!this.data.origin.latitude){this.selectComponent('#origin').choose();return}
    this.setData({loading:true,stage:loadingStages[0],items:[]})
    const timers=loadingStages.slice(1).map((stage,i)=>setTimeout(()=>this.setData({stage}),500*(i+1)))
    try { const data=await getApp().globalData.api.request({method:'POST',path:'/recommendations',data:buildRequest(this.data.filters,this.data.origin)}); this.setData({items:data.items,sessionId:data.session_id,fallback:data.source==='rules'}) }
    finally {timers.forEach(clearTimeout);this.setData({loading:false})}
  },
  async next(){const data=await getApp().globalData.api.request({method:'POST',path:`/recommendations/${this.data.sessionId}/next`});this.setData({items:data.items,fallback:data.source==='rules'})},
  toggleMore(){this.setData({showMore:!this.data.showMore})},
  openDetail(e){wx.navigateTo({url:`/pages/destination-detail/index?id=${e.detail.id}`})}
})
