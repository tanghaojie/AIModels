# AIModels 静态发布协议 v1

AIModels 拥有模型与配套资产，Cyber-Sight 消费发布清单。继续使用 `models/`、`model-assets/`、`tools/` 分类，不改变旧定位和验收记录。

## 文件与版本

- 根 `catalog.json`：`version: 1`、`updatedAt` 和 `models`，条目含稳定 `id`、`label`、`description`、可选 `thumbnail`、`manifest` 和质量选择用的 `variants`（id、label）。
- 各项目 `model.json`：版本、稳定 ID、展示信息、主模型 `model`、质量 `variants`、`placement`、`resources`、`attribution`。
- 资源 URL 相对所在 JSON 文件解析；模型与附件必须位于同一发布源。目录不包括参考资料目录、临时文件或未发布草稿。

`model` 和 variants 提供 `url`、`bytes`、`sha256`，variants 另有 `id`、`label`。`placement` 提供 `crs: EPSG:4326`、`coordinateSource: manifest`、`terrain: ellipsoid | any`、经纬度、椭球高 `height`、scale、heading/pitch/roll（度）与 `notice`。`height` 不得使用建筑本身高度，演示用 0 只适用于无真实地形场景，不声称实测。

resources 提供 `id`、`label`、`kind: 3d-tiles | geojson`、`url`、`required`；3D Tiles 可显式提供 `dayNight`，只用于本仓库已制作的兼容街区。署名条目为 text、url。配套资源通过模型组加载，不提供独立地标场景入口。

## 发布工作流

每个正式模型维护 `model.source.json`，填写模型文件、预览、定位来源或显式 placement、质量版本及配套资源。运行 `python tools/catalog/publish.py` 生成每模型描述和 catalog.json；`python tools/catalog/publish.py --check` 核对生成内容及已跟踪文件，验证 GLB/glTF 与 3D Tiles 的相对依赖。生成过程会计算主文件与质量版本的字节数及 SHA-256，不重写模型二进制、原始 placement 或 scene。

新增模型需加入 Git 后通过 check；参考图、Blender 源文件与脚本不作为场景资源自动加载。提交目录与发布描述，Vercel 继续静态托管。发布后验证 catalog、模型描述、模型文件及配套资源的 HTTP、类型和跨域头。

## 兼容和失败

消费端校验版本、唯一 ID、相对地址、坐标和资源类型；catalog 失败不影响手工 URL。目录加载以声明位置为准，不再重复询问 GLB 内坐标。必需资源失败整组回滚，可选配套失败保留主体并标注；取消清理本次资源，重复点击已加载项定位，整组显隐与移除。有配套的模型不能单独移动。地形不兼容先提示，不自动改变场景地形。

## 当前实施

2026-10-17：接入 8 个主模型项目；国家大剧院附 balanced/compatible 版本，台北 101 显式关联现有周边瓦片和来源署名。近似坐标/0 高程来自各项目原始元数据；cd-tower-gpt-56 的定位取自其 GLB scene extras。当前实现及验证结果见交付记录。
