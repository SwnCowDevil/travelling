# 个人页头像与筛选按钮对齐修复设计

## 目标

修复个人页头像在窄空间中被压缩为椭圆的问题，并使推荐筛选面板的“重置”“确定”按钮文字始终垂直居中。

## 根因

- 头像是 `me-hero` 弹性布局的子元素，默认 `flex-shrink: 1`，昵称区域占用空间增加时会压缩头像的水平方向。
- 筛选按钮使用固定 `line-height` 居中文本，小程序原生 `button` 的默认内边距会影响实际文字基线。

## 修复方案

### 头像

为 `.avatar` 明确设置不可收缩的弹性尺寸和盒模型：

- `flex: 0 0 132rpx`
- `min-width: 132rpx`
- `min-height: 132rpx`
- `box-sizing: border-box`

保留现有圆角、边框、浮动动画和图片 `aspectFill` 裁剪。

### 筛选操作按钮

为 `.panel-actions button` 使用弹性盒居中：

- `display: flex`
- `align-items: center`
- `justify-content: center`
- `padding: 0`
- `box-sizing: border-box`

保留 `76rpx` 高度、现有圆角和配色；移除依赖高度的 `line-height`。

## 测试

- 静态样式测试验证头像固定弹性尺寸、最小宽高和盒模型。
- 静态样式测试验证筛选按钮使用 flex 居中并清除默认内边距。
- 运行完整小程序测试。

## 非目标

- 不更改头像选择、头像图片来源或昵称布局。
- 不改变筛选按钮的点击处理、尺寸、配色或动画。
