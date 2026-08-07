function defaultAIForm() {
  return {
    token: '',
    base_url: 'https://www.packyapi.ai/v1',
    model: 'deepseek-v4-pro',
    group_note: 'deepseek-officially'
  }
}

function displayProfile(profile){return {mode:profile.mode,baseUrl:profile.base_url,model:profile.model,groupNote:profile.group_note,maskedToken:profile.masked_token,status:profile.connection_status}}
async function saveAfterConnectionTest(api,form){await api.request({method:'POST',path:'/ai-profile/test',data:form});return api.request({method:'PUT',path:'/ai-profile',data:form})}
module.exports={defaultAIForm,displayProfile,saveAfterConnectionTest}
