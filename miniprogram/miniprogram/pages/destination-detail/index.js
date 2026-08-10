const {buildDetailView}=require('./model')
Page({
  data:{view:{weatherDays:[],transport:[],weatherNotes:[],packing:[],cautions:[],highlights:[],foods:[],itinerary:[]},loading:true,regenerating:false,error:''},
  async onLoad(q){
    const api=getApp().globalData.api,id=q.id,month=Math.min(12,Math.max(1,Number(q.month)||new Date().getMonth()+1)),days=Math.min(7,Math.max(1,Number(q.days)||2)),originName=decodeURIComponent(q.origin_name||'当前位置')
    let preferences=[];try{preferences=JSON.parse(decodeURIComponent(q.preferences||'[]'))}catch(_){preferences=[]}
    this.guideContext={api,id,month,days,originName,preferences}
    try{
      const [destination,weather,guide]=await Promise.all([
        api.request({path:`/destinations/${id}`}),api.request({path:`/weather/${id}`}),
        api.request({method:'POST',path:`/guides/${id}`,timeout:120000,data:{month,days,origin_name:originName,preferences}})
      ])
      this.detailSource={destination,weather}
      this.setData({view:buildDetailView(destination,weather,guide,{days}),loading:false})
    }catch(error){this.setData({loading:false,error:error.message||'详情加载失败'})}
  },
  async regenerateGuide(){
    if(this.data.regenerating||!this.guideContext||!this.detailSource)return
    const {api,id,month,days,originName,preferences}=this.guideContext
    this.setData({regenerating:true})
    try{
      const guide=await api.request({method:'POST',path:`/guides/${id}`,timeout:120000,data:{month,days,origin_name:originName,preferences,force_refresh:true}})
      const {destination,weather}=this.detailSource
      this.setData({view:buildDetailView(destination,weather,guide,{days})})
      wx.showToast({title:'攻略已重新生成'})
    }catch(error){
      wx.showToast({title:error.message||'重新生成失败，请稍后重试',icon:'none',duration:2500})
    }finally{this.setData({regenerating:false})}
  }
})
