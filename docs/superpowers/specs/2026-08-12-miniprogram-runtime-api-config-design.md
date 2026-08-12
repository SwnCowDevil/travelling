# 小程序运行环境接口切换设计

## 目标

让微信开发者工具中的开发版继续连接本机 FastAPI，同时让体验版和正式版自动连接已上线的 `https://api.sunks.cc`，避免每次上传前手工修改配置。

## 方案选择

采用运行时自动识别微信小程序环境：

- `develop`：使用 `http://127.0.0.1:8000`，启用本地开发登录。
- `trial`：使用 `https://api.sunks.cc`，关闭本地开发登录。
- `release`：使用 `https://api.sunks.cc`，关闭本地开发登录。
- 无法读取环境时按 `develop` 处理，保证单元测试和本地工具兼容。

未采用的方案：

- 直接把现有地址写死为线上域名：实现最少，但会破坏本地一键调试。
- 上传前手工切换配置：容易忘记，正式包可能误连本机。

## 代码结构

配置模块提供一个纯函数，输入微信运行环境名称，输出 `apiBaseUrl` 和 `useDevAuth`。`app.js` 在启动时通过 `wx.getAccountInfoSync()` 获取 `envVersion`，解析运行配置后再创建 API 客户端和执行登录。

配置模块不保存 Token、AppSecret 或其他敏感信息。

## 错误处理

- `getAccountInfoSync` 不存在、抛错或没有返回 `envVersion` 时，回退到开发配置。
- 未知的环境名称也回退到开发配置，避免测试环境启动失败。
- 线上配置始终关闭开发登录，防止正式版绕过微信登录。

## 测试

- 验证 `develop` 返回本地地址并启用开发登录。
- 验证 `trial` 和 `release` 返回 HTTPS 域名并关闭开发登录。
- 验证缺失或未知环境回退到开发配置。
- 验证配置对象不包含 Token、Secret 或 API Key。

## 发布前置条件

- 在微信公众平台将 `https://api.sunks.cc` 加入 request 合法域名。
- 在服务器生产环境中补齐微信小程序 AppID 和 AppSecret。
- 用体验版验证微信登录、一键推荐、攻略生成与收藏流程。
