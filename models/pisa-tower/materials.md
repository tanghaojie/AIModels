# 材质、UV与灯光说明

全部材质连接实际Principled BSDF至Material Output。Blender5.2.1/标准glTF2.0 metallic-roughness；无Unlit、Transmission、Volume或GLB灯光依赖。材质默认单面，雕饰叶片使用显式前后表面。

| 材料 | 因子 | 纹理/UV/来源 |
| --- | --- | --- |
| Marble | metallic0，roughness来自ORM约0.69；Normal强度0.32 | 1024²原创marble-base/orm/normal PNG，UV0，4m平铺；BaseColor sRGB，ORM和OpenGL+Y Normal为Non-Color；ORM的G接roughness，R不声明AO绑定 |
| Carving | 浅暖石色，metallic0，roughness0.64 | 原创常量材质，几何雕饰；不声称雕刻扫描 |
| StoneGrey | 深灰绿石色，metallic0，roughness0.78 | 独立几何细带和菱形嵌饰 |
| Bronze | 0.21/0.27/0.17线性，metallic1，roughness0.43 | 铜钟形态、唇口、钟锤和支架为几何 |
| Iron / Wood | 铁metallic0.8/roughness0.6；木metallic0/roughness0.8 | 常量颜色、真实几何尺寸；无照片纹理 |
| Tile / Paving / Asphalt / Grass / Water | metallic0，roughness0.87/0.85/0.93/0.95/0.19 | 各1024²原创平铺PNG，UV0；无固定光照烘焙 |
| ivory/ochre/rose/cream | metallic0，roughness0.85 | 各1024²粉刷墙/百叶窗及固定稀疏窗灯，约16m宽×12m高重复；Emissive贴图sRGB，强度1.6作为源资产值 |
| DomeLead | metallic0.5，roughness0.64 | 金属屋面近似，非文保材料鉴定 |
| Leaves / LeavesDark / Bark | metallic0，roughness0.92–0.96 | 原创几何树冠/柏树形态，源树位为OSM；无需Alpha |
| WarmLight | 暖色Emissive，强度2.8 | 十二个场地固定灯片，标准emissiveFactor和KHR_materials_emissive_strength；不产生真实泛光 |

所有图片打包进 `.blend`，各GLB自包含图片。UV逐面以米制生成，曲面沿圆周展开；材质未引用不存在的UV。没有独占AO需求，因此无第二UV或虚构AO烘焙。未使用8K、KTX2或几何压缩。

最终导出的切线由 `canonical.py` 依据每个三角形UV、位置和法线顺序累加并正交化，保持OpenGL手性；位置、法线、UV、索引和图片不改。其目的为跨独立重建的字节稳定性，处理后重新通过Khronos Validator。

`PREVIEW_ONLY`有太阳、三个面积灯及背景地面，正式导出时全部排除。`scripts/render.py`的四种艺术照明：

| 构图/时段 | 太阳高度/能量 | 环境与泛光 | 曝光 |
| --- | --- | --- | --- |
| day | 48° / 3.0 | Nishita天空强度0.16；泛光1000W | -0.4EV |
| sunset | 7° / 2.2，暖光 | Nishita天空强度0.2；泛光1000W | -0.25EV |
| blue | -4° / 0 | 蓝色环境0.3；泛光22000W | +0.5EV |
| night | -15° / 0 | 深蓝环境0.32；泛光22000W | +0.8EV |

太阳方位为制作欧拉Z=-60°，非日期/地点星历计算；同构图是照明对照，不伪称真实绝对时刻。AgX、无HDRI依赖。EEVEE阶段图64采样；Cycles精修图32采样、降噪、最多6次反弹。镜头参数保存在源工程。源资产没有昼夜时钟、闪窗或与拼装进度联动的太阳动画。

夜景石材受光由Blender预览面积灯产生；基础PBR消费者无法仅靠GLB复现这一泛光。消费端实际效果、暗部可读性与性能仍需人工验收。详细Validator/因子/图像/UV检查见verification。
