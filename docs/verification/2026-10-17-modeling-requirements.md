# CS-AM-1 建模要求同步记录

日期：2026-10-17。交付对象为规范和模板，没有制作/改写模型、修改发布 Schema 或发布线上资产。

## 来源与对应文件

- 用户直接要求把引用会话的建筑动画要求补入 Cyber-Sight，再将材质、光照、爆炸动画、部件和位置写入 AIModels。
- `read_thread` 已读取会话 `6ad2cbc7-5560-83e9-a3c3-6afb06ff711e` 的两轮用户消息：建筑从无到有、构件逐步飞入拼装。助手正文仅为内容引用，原方案/脚本不可读取，不作为已取得的交付物。
- 当前依据包括 Cyber-Sight 制作/地理参考、统一渲染、DEV 拼装预览、AIModels 目录设计，以及本仓库发布 v1；基线分别为 `7e31597669306dd8e9d3c129018859b99dcdff5e` 和 `e913492a6616addd9c395667462270f7fd871ccf`。
- 新执行规范：[modeling-requirements.md](../modeling-requirements.md)；逐建筑模板：[model-brief.md](../templates/model-brief.md)；根 AGENTS.md 和 README 提供入口。标准 CS-AM-1，修订 2026-10-17。

## 同步边界

覆盖资料/几何、实际节点材质、UV/通道、预览与运行时照明、WGS84/高程/轴向、分件/枢轴/TRS、爆炸路径、飞入排程、单 clip 导出、脚本复现、预算/质量、文件与人工验收。规范同时说明未知高程在手工 URL 与发布目录的不同处理，以及动画附录不是现行目录接口。

没有改动旧 GLB、Blender 工程、model.source.json、model.json、catalog.json、发布工具、运行时或 tmp 样例。30 fps / 24 秒及其他范围是本次建议起点，不能归为原会话确认参数。

## 验证

初始 Git 暂存区为空，工作区干净。实际检查结果：

- 六份变更 Markdown 使用 Cyber-Sight 的 Prettier 配置格式化并检查通过；本仓库 21 个本地链接和 3 个 JSON 示例通过。
- 两仓库合计 17 份变更文档、323 个本地链接、4 个 JSON 示例通过；共同标准/修订、帧秒换算及构件时序一致。
- `python tools/catalog/publish.py --check` 通过：8 个模型、134 个模型/依赖文件；`git diff --check` 通过，变更只有 Markdown。
- Cyber-Sight 的 `pnpm format`、`pnpm format:check` 和归档 CI 通过，归档状态 NOT_DUE；相应设计、ADR、完成计划及协作日志已同步。

文档检查不等于 Blender 脚本、模型文件或 GPU/浏览器播放验收；实际资产由后续任务交付。未执行前端或浏览器自动化，也未推送/部署新内容。

## 提交追踪

Cyber-Sight 规范提交为 `4d950980d88af7eca24e86ebdcd0f931e58e0baf`，提交后归档 CI 仍为 NOT_DUE，GPT-6 trailer 已核验。本仓库提交由本文件和执行规范的 Git 历史追溯；本轮未要求推送或部署。
