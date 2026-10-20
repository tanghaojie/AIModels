# 建模参考资料

采集于 2026-10-20。`download-manifest.json` 记录原始 URL、文件、作者/机构、用途、分辨率和 SHA-256。

- [SOM 官方项目](https://www.som.com/projects/burj-khalifa/)：828 米高度、2010 年建成、三翼平面和螺旋退台；摄影原件 `originals/original-*.jpg`。摄影主要为 Nick Merrick / Hedrich Blessing；卫星图为 Go Eye Satellite。室内图仅为补充，不代表本项目制作了室内。
- [SOM 提供给 ArchDaily 的项目图纸](https://www.archdaily.com/882100/burj-khalifa-som)：`originals/som-plan.jpg`、`som-section.jpg`、`som-axonometric.jpg`。这些是真实建筑师图纸，不是生成图；未标尺寸部分与照片联合估算。
- CTBUH 两个历史 PDF 地址已失效，manifest 保留失败事实。本交付没有把未取得的论文当作已读依据；实际造型依据是上面三张 SOM 图纸和建成实景。
- `osm-context.json` 与 `overpass-query.txt`：可复现地图快照；查询范围略大于最终半径，生成阶段严格裁切 2000 米。实际源数据时间以 `osm3s.timestamp_osm_base` 为准，晚于该时间的变化未保证覆盖。

版权摄影/图纸和网页原件保存在本机 `originals/`、`pages/`，只用于建模研究及用户验收，未获得随 GitHub 再分发许可，因此由项目 `.gitignore` 排除。Git 克隆包含下载程序、来源、地图源数据和模型，不会自动带回摄影原件。运行 `scripts/acquire.py` 可以重新下载；来源失效时保留失败记录，不以别的图片冒充原件。

OSM 地图按 ODbL-1.0 分发；压缩快照同时存于 `model-assets/geo-context/burj-khalifa-2000-v1/sources/`。街区立面/植被/设备是程序化表现，真实轮廓与估算细部的区别见 metadata.json。
