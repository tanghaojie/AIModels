# 哈利法塔 · 高空拼装与 Downtown Dubai

Blender 5.2.1 LTS 制作，CS-AM-1，v1.0.0，2026-10-20。这是依据 [SOM 官方项目](https://www.som.com/projects/burj-khalifa/)和其提供的[平面/剖面/轴测图](https://www.archdaily.com/882100/burj-khalifa-som)进行的独立建筑可视化重建。不是测绘、施工 BIM 或官方数字孪生。

## 成品与动画

| 交付 | 文件 |
| --- | --- |
| 完整可编辑源工程，已打包纹理 | [burj-khalifa.blend](burj-khalifa.blend) |
| 静态完整成品 | [burj-khalifa.glb](burj-khalifa.glb) |
| 36 秒高空飞入组装后落地 | [burj-khalifa-assembly.glb](burj-khalifa-assembly.glb) |
| 14 秒分层/分翼爆炸 | [burj-khalifa-explode.glb](burj-khalifa-explode.glb) |
| 飞入视频 / 爆炸视频 | [assembly.mp4](previews/assembly.mp4) / [explode.mp4](previews/explode.mp4) |
| 作品展示板 | [portfolio.jpg](previews/portfolio.jpg) |
| 半径 2000 米街区 | [tileset.json](../../model-assets/geo-context/burj-khalifa-2000-v1/tileset.json) |
| 发布描述 / 制作任务书 | [model.json](model.json) / [model-brief.md](model-brief.md) |
| 部件 / 共同时间 / 材质 | [parts.json](parts.json) / [animation.json](animation.json) / [materials.md](materials.md) |

三翼弧边平面、螺旋退台、实体金属楼层带和竖框、机电层百叶、露台护栏、分段冠部及 828 米尖塔组成主体。静态/动画共用相同几何与材质。主体 885,354 三角形、276 组可运动逻辑构件；高于规范建议预算，是为近景和分解内侧保留的高精度例外。未测目标引擎 FPS/显存，不提供虚构兼容档。

拼装片段共同 t=0，源与 GLB 30 fps：0–1 秒空场；核心、楼层、三翼幕墙、冠部和入口错峰从空中向下飞入；25 秒前在离地 120 米装配完毕；25–27 秒悬停；27–32 秒整体平稳下降；32–36 秒完整成品保持。GEO_ROOT 始终固定，各部件以同一降落函数运动。爆炸 1.5–10 秒有序展开，保持至 14 秒。GLB 使用单一标准 TRS clip，默认节点姿态为完整成品。

视频是 1280×960、15 fps 检查预览，保留 36/14 秒真实时长；最终模型动画为 30 fps 核心 TRS 采样。动画不改变太阳日期或昼夜时钟。

## 场地与精度

以 [55.274375,25.197197] 为近似 WGS84 地面锚点，Blender +X 北/+Y 西/+Z 上，导出 glTF +X 北/+Y 上/+Z 东，单位米。真实椭球高未知，GLB 省略该字段；目录 height=0、terrain=ellipsoid 仅用于演示，不能当作实测地形高度。

街区使用 4241 个 OSM 建筑/建筑分段要素及 1 个鸟瞰近似补绘，不能将这个数量理解为 4242 栋独立建筑。OSM 快照实际基准时间为 2026-07-24T11:04:51Z，采集于 2026-10-20。1042 个要素有 height，176 个按楼层估算，3023 个按类型估算；立面、屋顶设备、车辆和植被为展示性细部。

Dubai Mall 的关系型主轮廓未能从公开接口下载，因此按已存 SOM 鸟瞰图和邻近 OSM 路网补绘近似体量，平面误差约 40–60 米、楼高 28 米为估算；后期扩建没有精确重建。细节见 [context-overrides.json](context-overrides.json)。其余周边没有用随机城市网格填补空缺。原始地图、排除主体的 ID、许可和统计见附件 [metadata.json](../../model-assets/geo-context/burj-khalifa-2000-v1/metadata.json)。

主体宽深、逐层标高、退台高度、内部墙体、入口及景观细部存在摄影/图纸估算，不等于建成尺寸认证。窗灯为固定遮罩、冷暖和暗区；玻璃为基础 PBR 不透明近似，保留金属/石材/混凝土等物理分类，无 Unlit、Transmission 或随机闪灯依赖。

## 参考与预览

26 份成功保存的摄影/图纸原件以及来源清单见 [references/](references/README.md)。版权原件在本机 `references/originals/`，未随 Git 再分发；Git 克隆含可复现下载程序与来源，不会自动包含摄影原件。原创纹理在 `textures/`，同时打包于源工程。CTBUH 历史 PDF 下载失败，未作为已读证据。

[日光](previews/day.png)、[日落](previews/sunset.png)、[蓝调](previews/blue.png)、[夜间](previews/night.png)使用同机位；另有 [入口](previews/entry.png)、[侧后方](previews/rear.png)、[俯瞰](previews/aerial.png)、[幕墙近景](previews/detail.png)、[完整街区](previews/district.png) 和 [Cycles 展示图](previews/beauty-sunset.png)。这些都是 Blender 渲染，不是实景照片或目标引擎截图。

预览光照位于独立 `BK_PREVIEW_ONLY`，包含相机、太阳、面积补光与地平面；不随 GLB 导出。AgX，日光太阳高度 43°、日落 6°、蓝调 -4°、夜间 -18°，分别是固定照明布景，未冒充某个绝对时刻的太阳测量。天空为 Blender 程序天空，无外部 HDRI。具体能量/方向、相机参数、采样写在 `scripts/render.py` 与 `verification/source.json`；Cycles 展示图使用 OptiX GPU、64 samples、降噪、6 bounces。

## 可复现命令

在仓库根运行，Python 3.12+，Blender 5.2.1，FFmpeg；`requirements.txt` 提供 Python 依赖，Node 验证器另需 `gltf-validator`。此轮制作设备为 RTX 3050 Laptop GPU 4 GiB；渲染成功不代表实际浏览器性能认证。

```powershell
python -m pip install -r models/burj-khalifa/requirements.txt
python models/burj-khalifa/scripts/acquire.py
python models/burj-khalifa/scripts/fetch_osm.py
python models/burj-khalifa/scripts/prepare.py
blender --background --factory-startup --python-exit-code 1 --python models/burj-khalifa/scripts/build_model.py
python models/burj-khalifa/scripts/export_animation.py
python models/burj-khalifa/scripts/audit.py
node models/burj-khalifa/scripts/validate.cjs
blender --background models/burj-khalifa/burj-khalifa.blend --python-exit-code 1 --python models/burj-khalifa/scripts/render.py -- stills
blender --background models/burj-khalifa/burj-khalifa.blend --python-exit-code 1 --python models/burj-khalifa/scripts/render.py -- stages
blender --background models/burj-khalifa/burj-khalifa.blend --python-exit-code 1 --python models/burj-khalifa/scripts/render.py -- beauty
blender --background models/burj-khalifa/burj-khalifa.blend --python-exit-code 1 --python models/burj-khalifa/scripts/render.py -- video
blender --background models/burj-khalifa/burj-khalifa.blend --python-exit-code 1 --python models/burj-khalifa/scripts/render.py -- explodevideo
python models/burj-khalifa/scripts/media.py
```

源快照已随项目/附件提供，无须每次联网；重跑应保留固定源快照来复现此版。`acquire.py` 会保留下载失败事实，不会替用户绕过来源限制。脚本只替换本项目场景/命名集合，推荐使用上面的独立后台工厂启动；不清空用户别的场景。`scripts/animate.py -- explode output.blend` 可将同一源工程切换到可编辑爆炸动画并另存。

## 验证与发布

最终二进制的 Khronos 检查、bytes/SHA-256、资源和动画通道统计在 [verification/summary.json](verification/summary.json)。核心检查包括唯一固定 GEO_ROOT、无预览灯/相机、嵌入纹理/UV、实际 PBR/Emissive 因子、单 clip、共同时间、持续向下的飞入、120 米整体下降、末帧保持与静态/拼装末态/爆炸首态相同。源工程检查见 [source.json](verification/source.json)，真实 Blender GLB 导入检查见 [blender-roundtrip.json](verification/blender-roundtrip.json)。

发布使用仓库 `tools/catalog/publish.py` 与 `--check`，静态为主文件，assembly/explode 为独立模式，默认 assembly。线上部署与完整字节/MIME/CORS/SHA-256 检查分别保存 `verification/deployment.json`、`verification/remote.json`。

Cyber-Sight 实际显示、昼夜过渡、3600 倍时钟、暂停/拖动/重播交互、设备 GPU/FPS 由维护者人工验收，本任务未运行前端或浏览器自动化。动画数值可随机采样不等于前端交互已验收；Blender 画面、Validator、部署成功分别记录。
