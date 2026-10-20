# Downtown Dubai · 半径 2000 米场景附件

主体锚点 [55.274375,25.197197]，局部 +X 北/+Y 上/+Z 东。街区使用 OpenStreetMap 的实际建筑/建筑分段、道路、湖面、绿地轮廓，AEQD 米制投影与圆形裁切。原始源数据按 ODbL 保存 `sources/`，出处/时间/高度估算数量见 `metadata.json`。

例外：Dubai Mall 主体未能从关系接口取得，按已保存的 SOM / Go Eye Satellite 鸟瞰图近似补绘，平面误差约 40–60 米、楼高 28 米为估算，不表示当前扩建后的精确轮廓。该项与 4241 个 OSM 建筑/分段要素分开记录，详见主体项目 `context-overrides.json`。

`district.glb` 为 Blender 导出、具基础 PBR/UV/静态窗灯的独立街区；`tileset.json` 使用正的顶层 geometricError=4000、叶误差=0、ECEF 北/西/上变换及覆盖范围包围体。作为主体 model.json 的必需 3d-tiles 资源发布，无独立地标目录项。

真实椭球高未知，展示高度 0，不代表实测地面或自动地形采样。缺失楼高按楼层/类型估算，立面、设备、树木和车辆为示意；没有以随机建筑体块填满空缺。前端实际显示、动态昼夜、GPU 及浏览器播放由维护者人工验收。

署名：© OpenStreetMap contributors，https://www.openstreetmap.org/copyright 。原创程序化材质与脚本：AIModels。
