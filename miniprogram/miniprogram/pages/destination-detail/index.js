const {buildDetailView}=require('./model')
Page({
  data:{view:{weatherDays:[],transport:[],weatherNotes:[],packing:[],cautions:[],highlights:[],foods:[],itinerary:[]},loading:true,regenerating:false,savingFavorite:false,favoriteId:0,generationMode:'fast',error:''},
  async onLoad(q){
    const api=getApp().globalData.api,id=q.id,month=Math.min(12,Math.max(1,Number(q.month)||new Date().getMonth()+1)),days=Math.min(7,Math.max(1,Number(q.days)||2)),originName=decodeURIComponent(q.origin_name||'当前位置')
    let preferences=[];try{preferences=JSON.parse(decodeURIComponent(q.preferences||'[]'))}catch(_){preferences=[]}
    this.guideContext={api,id,month,days,originName,preferences}
    try{
      const [destination,weather,guide,favorites]=await Promise.all([
        api.request({path:`/destinations/${id}`}),api.request({path:`/weather/${id}`}),
        api.request({method:'POST',path:`/guides/${id}`,timeout:60000,data:{month,days,origin_name:originName,preferences,generation_mode:'fast'}}),
        api.request({path:'/favorite-guides'})
      ])
      this.detailSource={destination,weather}
      this.guideResponse=guide
      const existing=(favorites.items||[]).find(item=>item.destination_id===Number(id))
      this.setData({view:buildDetailView(destination,weather,guide,{days}),favoriteId:existing?existing.id:0,generationMode:'fast',loading:false})
    }catch(error){this.setData({loading:false,error:error.message||'详情加载失败'})}
  },
  async regenerateGuide(){ return this.generateGuide(this.data.generationMode) },
  async generateGuide(mode='fast'){
    mode=typeof mode==='string'?mode:mode.currentTarget.dataset.mode
    if(this.data.regenerating||!this.guideContext||!this.detailSource)return
    const {api,id,month,days,originName,preferences}=this.guideContext
    this.setData({regenerating:true})
    try{
      const guide=await api.request({method:'POST',path:`/guides/${id}`,timeout:mode==='deep'?120000:60000,data:{month,days,origin_name:originName,preferences,generation_mode:mode,force_refresh:true}})
      const {destination,weather}=this.detailSource
      this.guideResponse=guide
      this.setData({view:buildDetailView(destination,weather,guide,{days}),generationMode:mode})
      wx.showToast({title:mode==='deep'?'深度攻略已生成':'快速攻略已生成'})
    }catch(error){
      wx.showToast({title:error.message||'重新生成失败，请稍后重试',icon:'none',duration:2500})
    }finally{this.setData({regenerating:false})}
  },
  async saveFavorite(){
    if(this.data.savingFavorite||!this.guideContext||!this.guideResponse)return
    if(this.data.favoriteId){
      wx.navigateTo({url:`/pages/favorite-guide-detail/index?id=${this.data.favoriteId}`})
      return
    }
    this.setData({savingFavorite:true})
    try{
      const favorite=await this.guideContext.api.request({method:'POST',path:'/favorite-guides',data:{destination_id:this.guideContext.id,generation_mode:this.data.generationMode,payload:this.guideResponse.payload}})
      this.setData({favoriteId:favorite.id})
      wx.showToast({title:'攻略已收藏'})
    }catch(error){
      wx.showToast({title:error.message||'收藏失败，请稍后重试',icon:'none'})
    }finally{this.setData({savingFavorite:false})}
  }
})
