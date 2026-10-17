# AIModels 模型发布目录交付

2026-10-17 完成版本 1 静态发布协议，消费端为 Cyber-Sight Geo 外部数据中的 AI 模型。

- 功能提交：`d9ff258dda025826cf3a408a7aa17389b9f4c108`。
- 跨平台排序修正：`37692bd32eebccd075d322b168037beb628bfc2c`；固定 casefold 字符串排序，避免 Windows/Linux Path 比较规则不同造成清单过期。
- 8 个模型描述，国家大剧院含两个质量版本，台北 101 声明配套街区及署名。
- 本地发布生成/校验通过，遍历 134 个模型/依赖文件；7 项发布工具回归检查通过。
- 修正提交的 [GitHub Actions 发布检查](https://github.com/tanghaojie/AIModels/actions/runs/38998039897) 已通过（Ubuntu / Python 3.12）。
- Vercel 已将功能提交发布为 READY；线上 catalog 与 8 份描述匹配本地文件。
- 10 个主模型/质量文件完整下载校验，字节数及 SHA-256 全部匹配；131 个配套瓦片、纹理和预览端点的 HEAD 请求通过。
- 本轮已检查的发布响应均为 HTTP 200，跨域头 `Access-Control-Allow-Origin: *`；详细 URL、类型与摘要见 [发布校验记录](verification/2026-10-17-catalog.json)。排序修正没有改变发布 JSON 或模型内容。

模型真实画面、昼夜及资源交互由维护者在 Geo 人工验收。线上文件可读及摘要一致不等于 GPU 渲染验收。
