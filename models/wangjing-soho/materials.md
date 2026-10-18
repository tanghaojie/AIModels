# 材质与光照清单

所有材料使用连接到 Material Output 的 Principled BSDF，GLB 为 metallic-roughness PBR；主体没有 Unlit、Transmission、Volume 或渲染器专用效果依赖。所有不透明面单面，玻璃用不透明镀膜近似并保留内部楼板遮挡。

| 材质 | 实际通道 / 尺度 | 参数与用途 |
| --- | --- | --- |
| Glass_lowE | 原创 1K `curtain-base/emissive/orm.png`，UV0；16×8 房间图集，单块对应一个几何幕墙段 | metallic 0；roughness G 通道约 0.17–0.27；冷暖不均匀窗灯与暗区固定分布 |
| Aluminium_white | 常量线性颜色约 (0.78,0.79,0.77) | 完整白色涂层 metallic 0 / roughness 0.28；真实闭合断面与圆角折面，分层几何，不是条纹贴图 |
| Frame / Soffit | 常量 | 裸金属框架 metallic 0.75 / roughness 0.28；底面粗糙度 0.4，区别于白铝 |
| Slab / Concrete | 常量 / 原创 1K `concrete-base.png` | metallic 0 / roughness 0.8；楼板厚 0.28 m，核心为展示构造 |
| Limestone | 原创 1K `limestone-base.png`，UV0，4 m 周期 | metallic 0 / roughness 0.73；铺装拼缝与轻微颗粒，不烘入日照 |
| Asphalt / Grass | 原创 1K 基色，UV0，米制平铺 | roughness 0.92 / 0.9；深色路面与层次绿地 |
| Water / Stone_dark | 常量 | 水面不透明近似，roughness 0.13；邻面反光来自预览环境，不承诺 GLB 自动照明 |
| Bark / Leaves_0..2 / Bench | 常量 | 分枝、非等大树冠、三种叶色、木色长椅；没有需要 alpha 的叶片薄片 |
| Landscape_light | 固定暖色自发光 | 地面边灯与庭院灯；GLB emissiveFactor 在标准范围内，强度使用 KHR_materials_emissive_strength |
| district office/residential/concrete facade | 原创共享 256 px Base/ORM/Emissive，UV0；约 12 m 周期 | 真实脚印上的示意立面，固定窗灯；不当作实景纹理 |
| Road_marking / Car_0..2 | 常量 | 真实路段上的示意标线与车辆，无交通仿真 |

图片颜色采用 sRGB，ORM 为 Non-Color。幕墙 UV 逐块映射并留图集边距，铺装与街区墙面用米制 UV。此任务未使用法线图或 AO 烘焙，不存在缺失的 Normal/AO 依赖。纹理由 `scripts/prepare.py` 生成，随源工程打包，GLB 图片自包含。

## Blender 预览

Blender 5.2.1 LTS，EEVEE、屏幕空间光线追踪、AgX，静帧默认 32 samples，1600×1100；另交付 `previews/beauty-day.png`，使用 Cycles 64 samples、去噪与 6 次最大反弹。预览独立在 `WJ_PREVIEW_ONLY` 集合中。视频为 EEVEE 8 samples、关闭屏幕空间追踪的轻量预览，照明与材质精修以静帧为准。

| 模式 | 太阳高度 / 旋转 | Sun energy | World strength | 曝光 |
| --- | --- | --- | --- | --- |
| 日景 | 35° / 300° | 2.5 | 0.12 | -0.2 |
| 日落 | 6° / 310° | 2.2 | 0.065 | +0.1 |
| 蓝调 | -4° / 220° | 0.08 | 0.25，冷蓝环境 | +1.0 |
| 夜景 | -15° / 240° | 0 | 0.12，冷蓝环境 | +1.4 |

日景/日落采用 Blender 5.2 Multiple Scattering 程序天空；没有外部 HDRI 依赖。太阳角直径 1°，独立圆形软箱位于 (-160,-100,300) m、直径 250 m，日景/日落功率 18000，蓝调/夜景 320000。这些是美术预览照明，不代表某一实测日期时刻的太阳位置。窗灯固定布局；脚本为同构图比较切换预览强度，没有第二套时钟或随机闪窗。

GLB 排除相机、Sun、软箱、天空；保留资产自身铺装、水景和景观。目标引擎需提供自己的环境与昼夜权重。静态 Emissive 不会自动照亮邻面；屏幕空间反射只属于 Blender 预览条件。
