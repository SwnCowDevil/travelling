function clone(value){return JSON.parse(JSON.stringify(value))}
const {favoriteSourceLabel}=require('../../utils/guide-source')
Page({
  data:{saved:null,draft:null,sourceLabel:'',editing:false,loading:true,saving:false,error:''},
  async onLoad(query){this.id=Number(query.id);await this.load()},
  async load(){try{const value=await getApp().globalData.api.request({path:`/favorite-guides/${this.id}`});this.setData({saved:value,draft:clone(value),sourceLabel:favoriteSourceLabel(value.source,value.user_edited),loading:false})}catch(error){this.setData({loading:false,error:error.message||'收藏攻略加载失败'})}},
  edit(){this.setData({draft:clone(this.data.saved),editing:true})},
  cancel(){this.setData({draft:clone(this.data.saved),editing:false})},
  input(event){this.setData({[`draft.payload.${event.currentTarget.dataset.field}`]:event.detail.value})},
  async save(){if(this.data.saving)return;this.setData({saving:true});try{const {draft}=this.data;const value=await getApp().globalData.api.request({method:'PUT',path:`/favorite-guides/${this.id}`,data:{generation_mode:draft.generation_mode,payload:draft.payload}});this.setData({saved:value,draft:clone(value),sourceLabel:favoriteSourceLabel(value.source,value.user_edited),editing:false});wx.showToast({title:'修改已保存'})}catch(error){wx.showToast({title:error.message||'保存失败，请稍后重试',icon:'none'})}finally{this.setData({saving:false})}},
  remove(){wx.showModal({title:'删除收藏',content:'删除后无法恢复，确定继续吗？',success:async result=>{if(!result.confirm)return;try{await getApp().globalData.api.request({method:'DELETE',path:`/favorite-guides/${this.id}`});wx.showToast({title:'已删除'});setTimeout(()=>wx.navigateBack(),400)}catch(error){wx.showToast({title:error.message||'删除失败',icon:'none'})}}})}
})
