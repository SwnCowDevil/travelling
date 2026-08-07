const {buildDetailView}=require('./model')
Page({
  data:{view:{weatherDays:[],transport:[],weatherNotes:[],packing:[],cautions:[],highlights:[],foods:[],itinerary:[]},loading:true,error:''},
  async onLoad(q){
    const api=getApp().globalData.api,id=q.id,month=Math.min(12,Math.max(1,Number(q.month)||new Date().getMonth()+1)),days=Math.min(7,Math.max(1,Number(q.days)||2)),originName=decodeURIComponent(q.origin_name||'当前位置')
    let preferences=[];try{preferences=JSON.parse(decodeURIComponent(q.preferences||'[]'))}catch(_){preferences=[]}
    try{
      const [destination,weather,guide]=await Promise.all([
        api.request({path:`/destinations/${id}`}),api.request({path:`/weather/${id}`}),
        api.request({method:'POST',path:`/guides/${id}`,data:{month,days,origin_name:originName,preferences}})
      ])
      this.setData({view:buildDetailView(destination,weather,guide,{days}),loading:false})
    }catch(error){this.setData({loading:false,error:error.message||'详情加载失败'})}
  }
})
