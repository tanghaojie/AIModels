# 参考原图与依据

采集日期：2026-10-18。`download-manifest.json` 保存每张原图的 URL、作者、用途、分辨率、字节数与 SHA-256。19 张照片和图纸已实际下载在本目录，不只是链接。

建筑设计归属 **Zaha Hadid Architects / CCDI**。本项目是独立的展示级重建，不是原设计事务所的 BIM、竣工模型或授权背书。

| 来源 | 本地文件 | 建模依据 |
| --- | --- | --- |
| [ZHA 官方项目](https://www.zha.com/projects/architecture/wangjing-soho?disclaimer=true) | `zha-aerial.webp`、`zha-ground.webp`、`zha-detail.webp` | 建成形体、玻璃与白色铝制水平遮阳带、入口与水景；Jerry Yin / SOHO China、Xue Liang、Virgile Simon Bertrand 摄影 |
| [THE PLAN 项目及署名 ZHA 图纸](https://www.theplan.it/eng/architecture/wangjing-soho-zaha-hadid) | `1_siteplan.jpg`、`2_floorplan.jpg`、`3_floorplan2.jpg` | 三塔与附属亭的组合、平面轮廓、场地流线；图片为公开的 900×540 像素展示图，不是可用于工程放样的 CAD |
| 同上 | `sectiona-a.jpg`、`sectionb-b.jpg`、`eastelevation.jpg`、`southelevation.jpg`、`westelevation.jpg` | 剖面、层带和冠部收分 |
| 同上 | `02-jl.jpg`–`09-vsb.jpg` | 多方向建成照片；Jerry Yin、Virgile Simon Bertrand / Alphaville.hk |
| [CTBUH / Skyscraper Center](https://www.skyscrapercenter.com/complex/280) | 本文与任务书记录参数 | T1 118 m、T2 127 m、T3 200 m；25、26、45 层 |
| [OpenStreetMap](https://www.openstreetmap.org/copyright) | `osm-context.json`；公开附件内另存 gzip 副本 | WGS84 塔楼脚印、北向、真实街路和周边轮廓；塔楼 way 327007845/846/847，P1 691614969，P2 461446738 |
| [Overture](https://docs.overturemaps.org/attribution/) | `overture/building.geojson`、`building_part.geojson`；公开附件内另存 gzip | 固定版本 2026-09-23.1，只补入与当前 OSM 不重叠的轮廓；含 [East Asian Buildings](https://doi.org/10.5281/zenodo.8174931) 数据 |

## 许可与本地留存

照片和 ZHA 图纸保留原作者版权。原图仅为用户本地研究、逐图验收保留，已由本项目 `.gitignore` 排除公开再分发；Git 中保留来源清单、哈希、用途和可复现下载脚本 `scripts/acquire.py`。Git 克隆并不自动包含这些受版权保护的原图。运行脚本可按清单重新取得，是否允许使用仍取决于各来源条款。

OSM 派生地理数据按 ODbL-1.0；Overture 按实际来源分别署名，East Asian Buildings 按 CC BY 4.0。公开发布对应的来源快照及配置，不把第三方地理数据纳入原创代码许可。

## 精度边界

- 塔高采用公开参数；塔楼脚印与方位来自 OSM，经局部等距投影转成米。公开图纸和照片用于曲率、逐层收分和建筑特征校准。
- 玻璃分格、铝板接缝、景观岛、长椅、树木、内部核心/楼板属于视觉重建或示意；第三个 6 m 低亭按总平面近似描绘。没有声称取得完整施工图、结构配筋或室内资料。
- 街区中 4 栋有源高度，58 栋按楼层估算，1411 栋按类型估算。高度统计保存在附件 `metadata.json`；真实轮廓不等于所有楼高真实。
- 绝对椭球高未知；GLB 省略 `ellipsoid_height_m`。目录和 3D Tiles 的 0 高程明确用于椭球演示，不当作实测地形。
