# Vercel 自动发布

本仓库采用与 sample-data 相同的无框架静态托管方式。2026-10-16 查询到 sample-data 的 Vercel 项目框架为 `null`，生产部署为 `READY`，现有生产域名包括 `sample-data-jt.vercel.app`。

## 首次连接 GitHub

1. 打开 [Vercel 新建项目](https://vercel.com/new)，选择管理 sample-data 的同一团队。
2. 在 Import Git Repository 中导入 `tanghaojie/AIModels`。如果看不到仓库，先在 GitHub 的 Vercel App 仓库权限中允许访问 AIModels。
3. Project Name 可设为 `aimodels`；最终域名以 Vercel 实际分配结果为准。
4. 设置以下参数，然后点击 Deploy。

| 配置项 | 值 |
| --- | --- |
| Framework Preset | `Other` |
| Root Directory | 仓库根目录，保持默认，不选择某个模型子目录 |
| Build Command | 开启 Override，留空 |
| Install Command | 留空；仓库配置已禁用安装 |
| Output Directory | `.` |
| Environment Variables | 当前无需配置 |

根目录 `vercel.json` 已显式设置 `framework: null`、空安装/构建命令、`outputDirectory: "."` 及跨域响应头。不要执行 Blender 建模或渲染脚本作为云端构建步骤。

## 自动发布分支

首次部署后，在项目 Settings 中确认 Git 仓库为 `tanghaojie/AIModels`，Production 环境的 Branch Tracking / Production Branch 为 `master`。不同界面版本可能将此入口放在 Environments → Production。

连接 Git 后，每次 push 到 `master` 会触发生产发布；其他分支和 PR 通常生成 Preview 部署。日常更新示例：

```powershell
git add .
git commit -m "feat(models): add a new building model"
git push origin master
```

这里无需额外配置 GitHub Actions、Deploy Hook 或 Vercel Token。

## 资源地址和跨域访问

发布成功后，使用实际生产域名拼接原相对路径，例如：

```text
https://<实际生产域名>/taipei-101/taipei-101.glb
https://<实际生产域名>/shanghai-tower/shanghai-tower.glb
https://<实际生产域名>/beijing-ncpa/beijing-ncpa-compatible.glb
```

保留目录及文件名大小写。原项目文档里的 sample-data 地址不会自动切换，使用时换成 AIModels 的生产域名。

如果资源需要供 Cesium / Cyber-Sight 直接加载，在 Settings → Deployment Protection 中确认生产地址允许匿名访问；sample-data 当前也未启用 SSO / 密码保护。配置中的 `Access-Control-Allow-Origin: *` 负责跨域访问，无法绕过登录保护。

当前仓库提供资源文件，没有根目录首页。根地址没有页面时，请直接检查具体 `.glb` 地址。

## 部署后检查

1. Vercel Deployments 显示目标提交为 `Ready`。
2. 使用生产域名访问具体 GLB，确认 HTTP 200、`Content-Type: model/gltf-binary` 和 `Access-Control-Allow-Origin: *`。
3. 下载远端文件，与本地 `Get-FileHash -Algorithm SHA256` 的结果比较。
4. 在实际 Cesium / Cyber-Sight 页面加载新地址，检查定位、比例与昼夜效果。项目里的历史验收记录不替代此次发布检查。

```powershell
curl.exe -I "https://<实际生产域名>/taipei-101/taipei-101.glb"
Get-FileHash -LiteralPath .\taipei-101\taipei-101.glb -Algorithm SHA256
```

## 官方文档

- [静态项目的构建与输出目录](https://vercel.com/docs/builds/configure-a-build)
- [GitHub 自动部署](https://vercel.com/docs/git/vercel-for-github)
- [项目配置](https://vercel.com/docs/project-configuration)
