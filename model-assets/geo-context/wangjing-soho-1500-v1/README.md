# 望京 SOHO 半径 1500 米街区

配套 `models/wangjing-soho`。中心 WGS84 116.47506° E / 39.99547° N，面积约 7.07 km²。源数据与处理脚本随仓库保留，统计见 `metadata.json`。

- `tileset.json`：3D Tiles 1.1，单块自包含 `district.glb`，约 8.2 万三角面。
- `scene.json`：来源与锚点说明。
- `sources/osm-context.json.gz`：2026-10-18 Overpass 快照。
- `sources/overture-buildings.geojson.gz`：固定 Overture 2026-09-23.1 数据。
- 主体三塔和两个 OSM 附属亭已排除，第三亭在模型项目中按图纸近似重建。
- 1463 栋地理轮廓、1210 个道路面、73 个绿地/水体面。只有 4 栋有源高度，58 栋按楼层估算，1411 栋按类型估算；不构成全街区精细测绘成果。

轮廓使用真实来源，不随机生成建筑。立面、窗灯、车辆和树木为示意。地面使用椭球体展示高程 0，禁止称为实测地形或自动适配任意地形。

OSM：© OpenStreetMap contributors / ODbL-1.0。[Overture attribution](https://docs.overturemaps.org/attribution/)；其中 East Asian Buildings 为 Qian Shi et al. / [CC BY 4.0](https://doi.org/10.5281/zenodo.8174931)。源数据许可不由原创脚本的许可替代。

生产消费端的昼夜、录屏与设备性能仍需维护者人工验收。本项目没有运行前端或浏览器自动化。
