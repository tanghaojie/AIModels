# AIModels

集中管理 AI 建筑建模项目：GLB 成品、Blender 源文件、建模与导出代码、定位数据、预览图和验收记录。

## 项目目录

| 分类 | 目录 | 内容 |
| --- | --- | --- |
| 模型 | `models/` | 完整模型项目，包括 GLB、Blender 源文件、项目脚本、参考资料和验收记录 |
| 模型附件 | `model-assets/` | 可独立复用的周边场景、空间数据及配套资源 |
| 工具 | `tools/` | 可复用的生成与校验工具 |

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

完整操作步骤及部署后检查见 [Vercel 自动发布说明](docs/vercel-deployment.md)。本次只准备配置与说明，尚未创建 AIModels 的 Vercel 项目。
