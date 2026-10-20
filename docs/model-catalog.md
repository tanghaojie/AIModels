# 模型与发布地址清单

程序消费 [catalog.json](../catalog.json)，模型描述为各项目 `model.json`；本文件仍供人阅读。生成与兼容规则见 [发布协议](publishing-protocol.md)。

记录日期：2026-10-21。

文件发布根地址：[https://jt-ai-models.vercel.app/](https://jt-ai-models.vercel.app/)（项目维护者提供）。以下按当前仓库目录及文件整理，发布 URL 不代表本次已逐项完成线上可用性验收。

## 分类子目录

| 分类 | 仓库目录 | 发布目录 |
| --- | --- | --- |
| 模型项目 | `models/` | [models/](https://jt-ai-models.vercel.app/models/) |
| 模型附件 | `model-assets/` | [model-assets/](https://jt-ai-models.vercel.app/model-assets/) |
| 通用工具 | `tools/` | [tools/](https://jt-ai-models.vercel.app/tools/) |

## 模型项目列表

当前共 12 个模型相关目录，其中 11 个包含主模型 GLB，1 个保存参考资料。同一建筑的不同项目分别保留。

| 模型 / 项目 | 本地子目录 | 发布目录 | 主模型文件地址 |
| --- | --- | --- | --- |
| 成都 OPPO 大厦（GPT-5.6 项目） | `models/cd-tower-gpt-56/` | [目录](https://jt-ai-models.vercel.app/models/cd-tower-gpt-56/) | [chengdu-oppo-tower.glb](https://jt-ai-models.vercel.app/models/cd-tower-gpt-56/chengdu-oppo-tower.glb) |
| 成都 OPPO 大厦 | `models/chengdu-oppo-tower/` | [目录](https://jt-ai-models.vercel.app/models/chengdu-oppo-tower/) | [chengdu-oppo-tower.glb](https://jt-ai-models.vercel.app/models/chengdu-oppo-tower/chengdu-oppo-tower.glb) |
| 上海环球金融中心 | `models/Shanghai-World-Financial-Center/` | [目录](https://jt-ai-models.vercel.app/models/Shanghai-World-Financial-Center/) | [shanghai-world-financial-center.glb](https://jt-ai-models.vercel.app/models/Shanghai-World-Financial-Center/shanghai-world-financial-center.glb) |
| 中央电视台总部大楼 | `models/cctv/` | [目录](https://jt-ai-models.vercel.app/models/cctv/) | [cctv-headquarters.glb](https://jt-ai-models.vercel.app/models/cctv/cctv-headquarters.glb) |
| 成都天府国际机场参考资料 | `models/成都天府国际机场/` | [目录](https://jt-ai-models.vercel.app/models/%E6%88%90%E9%83%BD%E5%A4%A9%E5%BA%9C%E5%9B%BD%E9%99%85%E6%9C%BA%E5%9C%BA/) | 当前无 GLB，保存参考图 |
| 成都天府国际机场 | `models/chengdu-tianfu-airport/` | [目录](https://jt-ai-models.vercel.app/models/chengdu-tianfu-airport/) | [chengdu-tianfu-airport.glb](https://jt-ai-models.vercel.app/models/chengdu-tianfu-airport/chengdu-tianfu-airport.glb) |
| 上海中心大厦 | `models/shanghai-tower/` | [目录](https://jt-ai-models.vercel.app/models/shanghai-tower/) | [shanghai-tower.glb](https://jt-ai-models.vercel.app/models/shanghai-tower/shanghai-tower.glb) |
| 台北 101 | `models/taipei-101/` | [目录](https://jt-ai-models.vercel.app/models/taipei-101/) | [taipei-101.glb](https://jt-ai-models.vercel.app/models/taipei-101/taipei-101.glb) |
| 北京国家大剧院 | `models/beijing-ncpa/` | [目录](https://jt-ai-models.vercel.app/models/beijing-ncpa/) | [beijing-ncpa.glb](https://jt-ai-models.vercel.app/models/beijing-ncpa/beijing-ncpa.glb) |
| 望京 SOHO | `models/wangjing-soho/` | [目录](https://jt-ai-models.vercel.app/models/wangjing-soho/) | [wangjing-soho.glb](https://jt-ai-models.vercel.app/models/wangjing-soho/wangjing-soho.glb) |
| 哈利法塔 | `models/burj-khalifa/` | [制作说明](https://jt-ai-models.vercel.app/models/burj-khalifa/README.md) | [burj-khalifa.glb](https://jt-ai-models.vercel.app/models/burj-khalifa/burj-khalifa.glb) |
| 比萨斜塔 · 奇迹广场 | `models/pisa-tower/` | [项目说明](../models/pisa-tower/README.md) | [pisa-tower.glb](https://jt-ai-models.vercel.app/models/pisa-tower/pisa-tower.glb) · [八向飞入](https://jt-ai-models.vercel.app/models/pisa-tower/pisa-tower-assembly.glb) · [爆炸](https://jt-ai-models.vercel.app/models/pisa-tower/pisa-tower-explode.glb) |

各模型的 Blender 源文件、定位数据、预览和使用限制见对应项目目录及 README。原项目中的历史 sample-data 地址与验收记录保留原样，当前 AIModels 地址以本清单为准。

## 哈利法塔动画与街区

哈利法塔另提供 [高空飞入拼装后落地](https://jt-ai-models.vercel.app/models/burj-khalifa/burj-khalifa-assembly.glb) 和 [爆炸分解](https://jt-ai-models.vercel.app/models/burj-khalifa/burj-khalifa-explode.glb)，通过 `modes` 发布。配套 [半径 2000 米街区](https://jt-ai-models.vercel.app/model-assets/geo-context/burj-khalifa-2000-v1/tileset.json) 含真实 OSM 轮廓与一项明确标注的 Dubai Mall 鸟瞰近似重建；详见项目验收边界。

## 国家大剧院其他 GLB 文件

| 文件 | 发布地址 | 用途 |
| --- | --- | --- |
| `beijing-ncpa-balanced.glb` | [下载](https://jt-ai-models.vercel.app/models/beijing-ncpa/beijing-ncpa-balanced.glb) | 减少树木和细小结构的均衡版本 |
| `beijing-ncpa-compatible.glb` | [下载](https://jt-ai-models.vercel.app/models/beijing-ncpa/beijing-ncpa-compatible.glb) | 减少内部肋架和景观的兼容版本 |

本地另有 `draft-original.glb`、`draft-no-backing.glb` 历史草稿，未纳入 Git，不列为发布文件。

## 模型附件与工具

| 内容 | 子目录 | 发布入口 |
| --- | --- | --- |
| 台北 101 周边场景 | `model-assets/geo-context/taipei-101-v1/` | [目录](https://jt-ai-models.vercel.app/model-assets/geo-context/taipei-101-v1/) · [scene.json](https://jt-ai-models.vercel.app/model-assets/geo-context/taipei-101-v1/scene.json) · [tileset.json](https://jt-ai-models.vercel.app/model-assets/geo-context/taipei-101-v1/tileset.json) |
| 望京 SOHO 半径 1500 米街区 | `model-assets/geo-context/wangjing-soho-1500-v1/` | [scene.json](https://jt-ai-models.vercel.app/model-assets/geo-context/wangjing-soho-1500-v1/scene.json) · [tileset.json](https://jt-ai-models.vercel.app/model-assets/geo-context/wangjing-soho-1500-v1/tileset.json) |
| 比萨斜塔半径 1000 米街区 | `model-assets/geo-context/pisa-1000-v1/` | [scene.json](https://jt-ai-models.vercel.app/model-assets/geo-context/pisa-1000-v1/scene.json) · [tileset.json](https://jt-ai-models.vercel.app/model-assets/geo-context/pisa-1000-v1/tileset.json) |
| 周边场景生成与校验工具 | `tools/geo-context/` | [目录](https://jt-ai-models.vercel.app/tools/geo-context/) · [README](https://jt-ai-models.vercel.app/tools/geo-context/README.md) |

周边场景的 `tiles/` 为场景分块 GLB，`materials/` 为材质资源，`sources/` 为来源空间数据，均归入模型附件。`tmp/` 为临时工作目录，不纳入正式模型清单。

## 地址维护规则

- 新增模型时，记录名称、准确的子目录、主 GLB 文件名及完整发布 URL。
- 文件改名或移动后同步更新清单；发布路径区分大小写，中文路径使用 URL 编码。
- 目录浏览取决于托管设置；实际加载模型时使用具体文件地址。
- 本地存在但未纳入 Git 的文件不会随 Git 自动发布。线上验收流程见 [Vercel 自动发布说明](vercel-deployment.md)。
