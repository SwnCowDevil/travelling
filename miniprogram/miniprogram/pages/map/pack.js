const META_KEY='travel.map-pack.meta.v1'

function readPack(wxApi,path){
  const text=wxApi.getFileSystemManager().readFileSync(path,'utf8')
  const pack=JSON.parse(text)
  if(!pack||!Array.isArray(pack.regions)||!pack.version)throw new Error('地图包格式不正确')
  return pack
}

function download(wxApi,url,onProgress){
  return new Promise((resolve,reject)=>{
    const task=wxApi.downloadFile({url,success:r=>r.statusCode===200?resolve(r.tempFilePath):reject(new Error('地图包下载失败')),fail:reject})
    if(task&&task.onProgressUpdate)task.onProgressUpdate(r=>onProgress(r.progress||0))
  })
}

async function ensureMapPack(wxApi,baseUrl,metadata,onProgress){
  const saved=wxApi.getStorageSync(META_KEY)
  if(saved&&saved.version===metadata.version){try{return readPack(wxApi,saved.filePath)}catch(_){wxApi.removeStorageSync(META_KEY)}}
  const tempPath=await download(wxApi,`${baseUrl.replace(/\/$/,'')}${metadata.download_path}`,onProgress)
  const pack=readPack(wxApi,tempPath)
  if(pack.version!==metadata.version)throw new Error('地图包版本不匹配')
  const savedPath=await new Promise((resolve,reject)=>wxApi.saveFile({tempFilePath:tempPath,success:r=>resolve(r.savedFilePath),fail:reject}))
  wxApi.setStorageSync(META_KEY,{version:metadata.version,filePath:savedPath})
  return pack
}

function mergeMapGeometry(items,regions){const byCode={};(regions||[]).forEach(region=>{byCode[region.region_code]=region});return(items||[]).map(item=>({...item,polygons:(byCode[item.region_code]||{}).polygons||[]}))}
module.exports={ensureMapPack,mergeMapGeometry}
