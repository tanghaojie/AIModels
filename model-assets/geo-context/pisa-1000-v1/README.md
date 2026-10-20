# 比萨斜塔半径1000米街区

入口`tileset.json`，3D Tiles1.1、正的顶层geometricError2000，叶内容district.glb，误差0。局部地面基准为斜塔OSM占地中心，经ECEF north/west/up变换定位；glTF标准Y-up转换后与主体一致。真实椭球高未知，使用0的椭球展示场景，非真实地形。

来自OpenStreetMap快照2026-10-20T15:50:57Z。2664个建筑轮廓、2027段源道路（合并同高重叠防止闪烁）、835个源树位。排除原斜塔relation/12982355，替换大教堂/洗礼堂/Camposanto为照片约束的展示模型。源高度、楼层及类型估算数量见metadata.json。实际屋脊、立面窗/百叶、树形与相邻地标细部是程序化重建，不是实景扫描。单内容发布，无瓦片LOD；实际GPU性能未测量。

完整可编辑场景与脚本在`models/pisa-tower/`。源码由固定配置与原始sources/osm-context.json.gz重建。保留数据署名 **© OpenStreetMap contributors · ODbL-1.0**，来源及许可：[OpenStreetMap](https://www.openstreetmap.org/copyright)。制作照片不包含在街区纹理中。
