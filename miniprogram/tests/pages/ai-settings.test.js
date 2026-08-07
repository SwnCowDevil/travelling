const test = require('node:test')
const assert = require('node:assert/strict')
const { defaultAIForm, displayProfile, saveAfterConnectionTest } = require('../../miniprogram/pages/ai-settings/model')

test('new AI form defaults to the available DeepSeek Pro model', () => {
  assert.equal(defaultAIForm().base_url, 'https://www.packyapi.ai/v1')
  assert.equal(defaultAIForm().model, 'deepseek-v4-pro')
})

test('profile exposes masked token only', () => {
  const shown = displayProfile({ mode:'personal', masked_token:'****6789', token:'secret' })
  assert.equal(shown.maskedToken, '****6789')
  assert.equal(shown.token, undefined)
})

test('failed connection test never replaces existing profile', async () => {
  const calls=[]
  const api={request: async value => {calls.push(value.path); if(value.path==='/ai-profile/test') throw new Error('failed')}}
  await assert.rejects(saveAfterConnectionTest(api,{token:'new'}))
  assert.deepEqual(calls, ['/ai-profile/test'])
})
