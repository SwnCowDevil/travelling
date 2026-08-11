const {filterItems}=require('./model')

Page({
  data:{
    items:[],visible:[],parentCode:null,status:null,
    statuses:[{key:null,label:'全部'},{key:'want',label:'想去'},{key:'visited',label:'去过'},{key:'revisit',label:'想再去'},{key:'avoid',label:'不想去'}]
  },
  onShow(){this.load()},
  async load(){
    try{
      const query=this.data.parentCode?`?parent_code=${this.data.parentCode}`:''
      const data=await getApp().globalData.api.request({path:`/map/summary${query}`})
      const items=data.items||[]
      this.setData({items,visible:filterItems(items,this.data.status)})
    }catch(_){
      wx.showToast({title:'足迹加载失败，请稍后重试',icon:'none'})
    }
  },
  filter(e){
    const status=e.currentTarget.dataset.status||null
    this.setData({status,visible:filterItems(this.data.items,status)})
  },
  drill(e){
    const code=e.currentTarget.dataset.code
    const level=e.currentTarget.dataset.level||(this.data.items.find(item=>item.region_code===code)||{}).level
    if(level!=='province'){
      if(wx.showToast)wx.showToast({title:'已到市级列表',icon:'none'})
      return
    }
    this.setData({parentCode:code})
    this.load()
  },
  backToCountry(){
    if(!this.data.parentCode)return
    this.setData({parentCode:null})
    this.load()
  },
  openVisits(){wx.navigateTo({url:'/pages/visit-records/index'})}
})
