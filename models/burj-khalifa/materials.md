# 材质与交换说明

全部材质实接 Principled BSDF → Material Output，关闭全局双面。最终导出因子、图片绑定和扩展以 `verification/materials.json` 为准。

| 材料 | 通道与参数 | 尺度、用途及边界 |
| --- | --- | --- |
| Glazing | metallic 0；roughness 约 0.19–0.27；Base Color、ORM、Emissive 1024² | 低辐射镀膜玻璃的不透明显示近似；1.5×3.8 米窗格。固定冷暖窗灯、窗帘和暗区，非全透明空壳，无 Transmission 依赖 |
| Stainless / Aluminium / Steel | metallic 1；roughness 0.27 / 0.32 / 0.36 | 实体楼层带、竖框、栏杆、冠部；常量 PBR，无 Unlit |
| Concrete / Slab / Roof | metallic 0；roughness 0.82–0.84 | 核心、楼板内侧和屋面；结构为展示示意，非实际钢筋/施工 BIM |
| Travertine | 1024² Base Color，roughness 0.74 | 原创石材颗粒与板缝，UV 每 4 米重复；入口/场地 |
| Asphalt / Sand / Grass | 1024² Base Color，roughness 0.94–0.95 | 原创程序化纹理，不含固定太阳光/整栋投影 |
| Water | metallic 0，roughness 0.18 | 源地图湖面，基础 PBR 近似；不保证目标引擎真实城市反射 |
| Warm_light | 暖白 Emissive，强度通过扩展 | 场地灯带随固定场地；仅表现灯位，不声称产生真实邻面受光 |
| 街区 facade | 原创平铺 base/ORM/emissive 图集 | 办公/住宅/混凝土类型，窗灯固定，不是各栋实景贴图 |

图像材质均使用 TEXCOORD_0；Base Color/Emissive 为 sRGB，ORM 为 Non-Color，G=roughness/B=metallic。没有使用法线图或独占 AO，因此不存在未提供的法线/AO 依赖；曲面、横带和近景主要由几何表现。不存在第二 UV 的强制需求。

窗灯标准 emissiveFactor 保持 0–1，额外强度使用 `KHR_materials_emissive_strength`，源 GLB 不含本地时钟或动画闪窗。Blender 四种灯光的 emissive 权重用于证据渲染；实际 Cyber-Sight 昼夜由维护者手动检查唯一 viewer.clock 的权重效果。

纹理全部为 AIModels 原创程序化图，不使用有版权的摄影贴图；种子与程序保留。source `.blend` 内打包全部纹理，外部 PNG 也交付，可独立修改。
