# 暂时隐藏灰狐 Loading 设计

## 目标

暂时停止在小程序 Loading 状态中显示灰狐 GIF，保留统一 Loading 组件、加载文案、业务状态与 GIF 资源，方便后续重新设计后快速恢复。

## 实现边界

- 从 `components/loading-stage/index.wxml` 移除 GIF `<image>` 节点。
- `loading-stage` 继续渲染调用页面传入的文字，并保留淡入动画。
- 缩小组件上下留白，使纯文字 Loading 不占用原 GIF 的空间。
- 保留 `compact` 属性，继续控制收藏页等紧凑场景的字号和间距。
- 保留 `assets/images/loading-gray-fox.gif` 文件，不删除、不修改、不加载。

## 页面行为

推荐页、目的地详情、快速/深度攻略生成、收藏列表和收藏详情继续使用统一 `loading-stage`。页面现有的 `loading`、`regenerating`、错误处理和防重复提交逻辑全部不变。

按钮级原生 Loading 与骨架屏继续保留，不受本次调整影响。

## 性能与恢复

WXML 不再引用 GIF 后，小程序运行时不会为这些 Loading 状态解码或播放动画。资源仍随代码保留；后续恢复时只需在统一组件中重新加入图片节点，不需要修改调用页面。

## 测试

- 验证 `loading-stage` 不包含 GIF 图片节点或 GIF 路径。
- 验证组件仍渲染 Loading 文案并支持 `compact` 属性。
- 验证 GIF 文件仍存在且保持 GIF 格式。
- 验证各页面仍使用统一组件，按钮 Loading 和骨架屏未被移除。
- 运行完整小程序测试。

## 非目标

- 不删除 GIF 文件。
- 不撤销各页面的统一组件接入。
- 不修改任何 API、请求流程或后端逻辑。
