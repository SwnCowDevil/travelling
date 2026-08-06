const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')

const projectRoot = path.resolve(__dirname, '../..')
const project = require('../../project.config.json')

test('developer tools can map root npm packages into miniprogramRoot', () => {
  assert.equal(project.setting.packNpmManually, true)
  assert.deepEqual(project.setting.packNpmRelationList, [{
    packageJsonPath: './package.json',
    miniprogramNpmDistDir: './miniprogram/'
  }])
  assert.equal(fs.existsSync(path.join(projectRoot, 'package.json')), true)
  assert.equal(
    path.resolve(projectRoot, project.setting.packNpmRelationList[0].miniprogramNpmDistDir),
    path.resolve(projectRoot, project.miniprogramRoot)
  )
})
