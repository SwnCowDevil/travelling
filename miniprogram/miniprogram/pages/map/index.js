const {filterItems,projectMapItems,hitRegion,visibleMapItems}=require('./model')
const {ensureMapPack,mergeMapGeometry}=require('./pack')

Page({
  data:{
    items:[],summaryItems:[],visible:[],projected:[],parentCode:null,status:null,mode:'list',
    mapAvailable:true,geometryAvailable:false,canvasReady:false,mapDownloading:false,mapProgress:0,
    statuses:[{key:null,label:'全部'},{key:'want',label:'想去'},{key:'visited',label:'去过'},{key:'revisit',label:'想再去'},{key:'avoid',label:'不想去'}]
  },
  onShow(){this.load()},
  onReady(){this.initCanvas()},
  async load(){
    try{
      const query=this.data.parentCode?`?parent_code=${this.data.parentCode}`:''
      const data=await getApp().globalData.api.request({path:`/map/summary${query}`})
      const summaryItems=data.items||[]
      const items=this.mapPack?mergeMapGeometry(summaryItems,this.mapPack.regions):summaryItems
      const visible=filterItems(items,this.data.status)
      const mode=this.data.mode
      this.setData({summaryItems,items,visible,geometryAvailable:Boolean(this.mapPack),mapAvailable:true,mode})
      if(mode==='map')this.drawMap()
    }catch(_){this.setData({mapAvailable:false,geometryAvailable:false,mode:'list'})}
  },
  initCanvas(){
    if(!wx.createSelectorQuery)return
    wx.createSelectorQuery().select('#footprint-canvas').fields({node:true,size:true}).exec(result=>{
      const item=result&&result[0]
      if(!item||!item.node||!item.width||!item.height)return
      const dpr=(wx.getSystemInfoSync&&wx.getSystemInfoSync().pixelRatio)||1
      item.node.width=item.width*dpr
      item.node.height=item.height*dpr
      const context=item.node.getContext('2d')
      context.scale(dpr,dpr)
      this.canvas={context,width:item.width,height:item.height}
      this.setData({canvasReady:true})
      if(this.data.mode==='map')this.drawMap()
    })
  },
  drawMap(){
    if(!this.canvas)return
    const {context,width,height}=this.canvas
    const projected=projectMapItems(visibleMapItems(this.data.items,this.data.status),width,height,18)
    context.clearRect(0,0,width,height)
    context.fillStyle='#0b1d2b'
    context.fillRect(0,0,width,height)
    for(const item of projected){
      context.beginPath()
      for(const path of item.paths){
        path.forEach((point,index)=>index?context.lineTo(point.x,point.y):context.moveTo(point.x,point.y))
        context.closePath()
      }
      context.fillStyle=item.color
      context.globalAlpha=item.map_status?0.84:0.42
      context.fill()
      context.globalAlpha=1
      context.strokeStyle='#72e2db'
      context.lineWidth=1
      context.stroke()
      const point=item.paths[0][0]
      context.fillStyle='#dffaf6'
      context.font='12px sans-serif'
      context.fillText(item.name,point.x+4,point.y+15)
    }
    this.setData({projected})
  },
  toggleMode(){
    if(this.data.mode==='map'){this.setData({mode:'list'});return}
    this.requestMapMode()
  },
  requestMapMode(){
    const open=()=>{this.setData({mode:'map',geometryAvailable:true,items:mergeMapGeometry(this.data.summaryItems,this.mapPack.regions),visible:filterItems(mergeMapGeometry(this.data.summaryItems,this.mapPack.regions),this.data.status)},()=>this.initCanvas())}
    if(this.mapPack){open();return}
    wx.showModal({title:'下载离线地图包',content:'下载一次后可离线查看中国地图，是否继续？',success:async result=>{
      if(!result.confirm)return
      this.setData({mapDownloading:true,mapProgress:0})
      try{const api=getApp().globalData.api,metadata=await api.request({path:'/map/pack'});this.mapPack=await ensureMapPack(wx,getApp().globalData.apiBaseUrl,metadata,progress=>this.setData({mapProgress:progress}));this.setData({mapDownloading:false});open()}
      catch(_){this.setData({mapDownloading:false,mode:'list'});wx.showToast({title:'地图包下载失败，可稍后重试',icon:'none'})}
    }})
  },
  filter(e){
    const status=e.currentTarget.dataset.status||null
    this.setData({status,visible:filterItems(this.data.items,status)})
    if(this.data.mode==='map')this.drawMap()
  },
  drill(e){
    const code=e.currentTarget.dataset.code
    const level=e.currentTarget.dataset.level||(this.data.items.find(item=>item.region_code===code)||{}).level
    if(level!=='province'){
      if(wx.showToast)wx.showToast({title:'已到市级地图',icon:'none'})
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
  tapMap(e){
    const point=e.detail||{}
    const item=hitRegion(this.data.projected,point.x,point.y)
    if(item&&item.level==='province')this.drill({currentTarget:{dataset:{code:item.region_code,level:item.level}}})
  },
  openVisits(){wx.navigateTo({url:'/pages/visit-records/index'})}
})
