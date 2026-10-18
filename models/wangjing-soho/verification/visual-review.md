# Blender 制作验收记录

日期：2026-10-18。以下是 Blender 资产侧证据，不是 Cyber-Sight 浏览器验收。

## 已实际查看的画面

- `previews/beauty-day.png`：Cycles 64 samples、去噪、1600×1100。检查三塔轮廓、SOHO 示意字样、水平铝带、入口低亭、地面接触与投影。
- `previews/day.png / sunset.png / blue.png / night.png`：EEVEE 同构图。幕墙、白铝、路面可区分；夜间冷暖窗口和暗区固定分布，景观边灯保持独立。
- `previews/low.png / rear.png / aerial.png / detail.png / district.png`：低机位、侧后、鸟瞰、幕墙近景及半径 1500 米街区。
- `previews/assembly-contact.jpg`：0 / 4 / 7.5 / 15 / 20 / 22 / 24.5 / 27 / 30 秒。空场保留街区与景观；构件由上向下进入，结构先行、幕墙后装；22 秒高空完整成品，27 秒落地，30 秒保持。
- `previews/explode-contact.jpg`：0 / 3 / 6 / 9 / 12 秒，楼板分层和幕墙分区展开，末态保持。

近景发现并已修正：上部核心筒位置随收分偏移并缩窄，避免露出外壳；冠部内缩上限按截面最小半径限制，避免翻折尖刺；竖框连接幕墙上下端实际坐标，避免斜幕墙上的悬空竖条。

画面是展示级重建。曲率和景观不是施工图复原，内部构造为示意，街区多数楼高为估算。远景地面为预览辅助面，正式 GLB 已排除。渲染存在程序天空/地平线的美术近似，不宣称实拍级还原。

## 文件和时间证据

- `summary.json`：静态、拼装、爆炸与街区四份 Khronos 结果，0 错误/0 警告。仅过滤常量材质未消费 UV 的 UNUSED_OBJECT 信息。
- `motion-audit.json`：逐帧几何包围范围、依赖、随机进度/暂停/重播纯函数审计，峰值 404 个运动件；不把示意套接解释为物理无碰撞施工。
- `blender-roundtrip.json`：实际把导出的拼装 GLB 导回 Blender，在 10 个时间点读取世界变换；最大位置误差 0.00001526 m，低于 1 mm。
- 静态与动画的网格、材质、图像、原始几何二进制一致；动画默认姿态为完整成品；首末文件姿态差为 0。地理锚点没有动画轨道。
- `source.json`：实际源工程场景、打包图片、fps 与轨道数量；原有用户 Blender 场景仍保留在实况应用。

## 边界

未运行 Cyber-Sight 前端或浏览器自动化。实际 Cesium 昼夜权重、地形、3600 倍时钟、GPU 内存、首次 ready 和实际播放帧率待维护者人工验收。目录 v1 不自动控制拼装/爆炸 clip。

视频的 10 fps 图像采样用于轻量预览，编码容器为 30 fps；源工程和 GLB 均保留完整 30 fps 采样。视频有 OSM / Overture / East Asian Buildings 署名，不能把预览采样率当成目标设备实时帧率。
