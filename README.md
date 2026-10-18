# AIModels

集中管理 AI 建筑建模项目：GLB 成品、Blender 源文件、建模与导出代码、定位数据、预览图和验收记录。

## 后续建模要求

新建筑或明确委托重制前，先阅读 [CS-AM-1 建模详细要求](docs/modeling-requirements.md)，将[逐建筑任务书](docs/templates/model-brief.md)复制到模型项目填写。要求覆盖资料与几何、PBR/UV/纹理、昼夜光照、WGS84/高程/朝向、部件与枢轴、爆炸分解、从无到有的飞入拼装、脚本、导出与验收。

默认分别交付完整静态 GLB、拼装动画 GLB、爆炸动画 GLB 和可编辑源工程；部件/时间附录供制作与验收使用。现行发布目录仍使用静态成品和质量版本，不会因新增文档自动获得通用动画控制。既有模型与历史验收未因此重制，见[本次同步记录](docs/verification/2026-10-17-modeling-requirements.md)。

## 发布地址与模型清单

文件发布根地址：[https://jt-ai-models.vercel.app/](https://jt-ai-models.vercel.app/)。文件地址按“发布根地址 + 仓库相对路径”组成，保留目录及文件名大小写。

各分类子目录、模型项目、GLB 文件及完整发布地址见 [模型与发布地址清单](docs/model-catalog.md)。新增模型或调整文件路径时，同步更新该清单。

程序读取入口为 [catalog.json](https://jt-ai-models.vercel.app/catalog.json)，每个模型的 `model.json` 声明定位、质量版本和配套资源。维护步骤见 [静态发布协议](docs/publishing-protocol.md)：新增/调整 `model.source.json` 后执行 `python tools/catalog/publish.py`，再执行 `python tools/catalog/publish.py --check`。CI 会核对清单、Git 跟踪文件、文件摘要及嵌套瓦片/纹理引用。

## 项目目录

| 分类     | 目录            | 内容                                                                 |
| -------- | --------------- | -------------------------------------------------------------------- |
| 模型     | `models/`       | 完整模型项目，包括 GLB、Blender 源文件、项目脚本、参考资料和验收记录 |
| 模型附件 | `model-assets/` | 可独立复用的周边场景、空间数据及配套资源                             |
| 工具     | `tools/`        | 可复用的生成与校验工具                                               |

```text
models/
  cd-tower-gpt-56/
  chengdu-oppo-tower/
  Shanghai-World-Financial-Center/
  cctv/
  成都天府国际机场/
  chengdu-tianfu-airport/
  shanghai-tower/
  taipei-101/
  beijing-ncpa/
  wangjing-soho/
model-assets/
  geo-context/
tools/
  geo-context/
```

各项目的使用方式、参考来源及限制见其自身 README、定位文件与验证记录。后续新模型在 `models/` 下新建独立项目目录，通用附件放入 `model-assets/`，通用工具放入 `tools/`。各模型项目内部文件保持在一起，便于项目内相对路径继续使用。

分类后的发布地址带相应目录前缀，例如 `/models/taipei-101/taipei-101.glb` 和 `/model-assets/geo-context/taipei-101-v1/scene.json`。历史 sample-data 发布地址保留原样。

## 首次迁移

2026-10-16 从 `tanghaojie/sample-data` 的工作区复制，来源提交为 `1c492dd`。以 `cd-tower-gpt-56` 的目录创建时间为起点，包含该目录及之后创建的全部 11 个目录。

- 本地完整复制 422 个文件，共 605,917,731 字节（577.85 MiB），逐文件 SHA-256 一致。
- 保留各项目原有 `.gitignore`。来源仓库已跟踪的 322 个文件纳入本仓库；其余 100 个原本被忽略的参考资料、备份、草稿、日志及打包文件保留在本地，不随 Git 克隆分发。
- `sample-data` 原文件保留。较早的 `apartment`、`cd-buildings`、`my-home`、`rc`、`shp-factory`、`test` 不在本次范围。
- 本次导入当前文件快照，未导入原仓库提交历史。原项目内的旧仓库路径、旧发布地址和验收记录保持原样，代表迁移前的历史证据，不代表 AIModels 已发布或完成线上验收。

## Vercel 静态发布

仓库根目录的 `vercel.json` 配置直接托管静态文件，跳过安装与构建，并允许浏览器跨域读取资源。代码和 `.blend` 源文件也属于静态输出范围。

发布根地址为 [https://jt-ai-models.vercel.app/](https://jt-ai-models.vercel.app/)。完整操作步骤及部署后检查见 [Vercel 自动发布说明](docs/vercel-deployment.md)。
