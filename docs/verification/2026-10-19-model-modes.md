# 模式、精细度与默认配置适配

维护者要求在 AIModels 添加模式/精细度声明，未声明使用默认配置，并适配 Sight。基线 AIModels bc5be67、Sight ba0b3ca；本轮不重制或修改模型二进制，不推送或部署。

采用发布 v1 可选字段兼容扩展：静态 model/variants 保留，modes 声明 assembly/explode 及各自 variants，defaultMode/defaultVariant 可选。默认 static/original，静态和动画的精细度不相互继承。非法声明拒绝，不猜测文件名或读取制作附录。

望京 SOHO 复用既有飞入和爆炸 GLB，国家大剧院保留三档并显式声明默认；其余源配置保持未声明，验证生成器缺省行为。全部生成清单保留旧字段并增加规范化默认值与模式摘要。

发布器 13 项检查已通过，包括旧配置、模式精细度独立、默认引用、重复/未知模式、缺失/未跟踪/远端文件和既有嵌套依赖检查。完整生成及 check 已覆盖 9 个模型和 139 个模型/依赖文件；新增的两种动画纳入摘要及依赖校验。未修改任何模型二进制、定位或街区资源。

最终验证：`python -m unittest discover -s tools/catalog -v`、`python tools/catalog/publish.py --check`、修改的 Markdown/源 JSON 按 Sight 配置执行 Prettier 检查及 `git diff --check` 均通过。生成 JSON 保持发布器确定性格式；提交通过 Git 历史按本记录路径追溯。Sight 设计/计划/日志与兼容扩展 ADR 维护于其 Platform 作用域。

Sight 不创建或运行前端/浏览器自动化；工程检查不代表实际 GPU、播放、定位、昼夜与交互视觉验收。
