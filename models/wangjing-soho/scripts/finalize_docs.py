"""Fill the task brief and delivery README from the actual asset evidence."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def main():
    summary=json.loads((ROOT/'verification'/'summary.json').read_text())
    motion=json.loads((ROOT/'verification'/'motion-audit.json').read_text())
    counts=json.loads((ROOT/'verification'/'build.json').read_text())
    rows='\n'.join(f"| `{Path(r['file']).name}` | {r['bytes']:,} | {r['triangles']:,} | {r['nodes']} / {r['primitives']} | {r['errors']} / {r['warnings']} |" for r in summary['reports'])
    brief=f'''# 望京 SOHO 建模任务书

本任务从 `docs/templates/model-brief.md` 复制后按实际制作填写。标准 [CS-AM-1](../../docs/modeling-requirements.md)，修订 2026-10-17。

## 1. 项目与交付范围

`wangjing-soho` / 北京望京 SOHO，2026-10-18，Blender 5.2.1 LTS，独立展示级重建。建筑设计 Zaha Hadid Architects / CCDI，建成状态参考 2014–2023 照片，资料采集 2026-10-18。

交付三塔与三座低亭、曲面幕墙、闭合白铝遮阳带、楼板/核心示意、入口、景观、窗灯、静态 GLB、飞入拼装 GLB、爆炸 GLB、可编辑 `.blend`、脚本及原图。周边半径 1500 m，约 7.07 km²，独立 3D Tiles 附件。

静帧 1600×1100；动画源 30 fps；视频预览 960×660，以 10 fps 采样同一时间轴。目标 Cyber-Sight / Cesium；实际设备播放性能与前端验收保留给维护者人工检查。

## 2. 资料、尺寸与来源

| 项目 | 依据与实际值 |
| --- | --- |
| 三塔高度 / 层数 | T1 118 m / 25，T2 127 m / 26，T3 200 m / 45；ZHA 与 CTBUH 公开参数 |
| 工作脚印、北向 | OSM ways 327007845 / 846 / 847，局部等距投影；非测绘精度 |
| 外轮廓、逐层收分、入口 | THE PLAN 所刊署名 ZHA 平面/立面/剖面及官方建成照片；曲率为拟合重建 |
| 低亭 | P1/P2 OSM 脚印，15 m 高；第三亭 6 m，按总平面近似描绘 |
| 参考原图 | 19 张已下载，`references/download-manifest.json` 有来源、作者、用途、许可和哈希 |
| 周边街区 | 1463 栋真实脚印、1210 道路面、73 绿地/水体面；OSM + Overture 2026-09-23.1 无重叠补充 |
| 高度不确定性 | 街区 4 栋源高度、58 栋楼层估算、1411 栋类型估算；不把真实轮廓等同于真实楼高 |
| 内部与景观 | 核心、楼板、分格、场地岛、树、车、灯具为展示构造；非 BIM / 施工模拟 |

照片与图纸仅本地保留，公开 Git 保存获取脚本及来源清单，不再分发受版权保护的原图。地理来源快照及署名公开保留。

## 3. 地理位置与局部基准

WGS84 参考锚点 116.47506° E / 39.99547° N。唯一固定 `GEO_ROOT` 在场地地面基准，Blender +X 北 / +Y 西 / +Z 上；导出 glTF +X 北 / +Y 上 / +Z 东。单位米、scale=1、heading/pitch/roll=0。

绝对椭球高未知：GLB metadata 省略 `ellipsoid_height_m`，`height_source=terrain_at_load`。目录明确 `terrain=ellipsoid`、`height=0` 且附 notice，3D Tiles 同锚点同基准；0 只是演示值，不能当作真实地形高度或宣称已自动贴地。

主模型装配包围盒（glTF 米）为 {summary['reports'][0]['lo']} 至 {summary['reports'][0]['hi']}。包含场地，主体最高 200 m。坐标只写 GEO_ROOT，不写入部件。

## 4. 材质、纹理与 UV

详见 [materials.md](materials.md)。实际 Principled 输出、PBR 基色/金属/粗糙度、自发光及纹理绑定已读取最终 GLB 验证。玻璃 metallic=0 的不透明低辐射镀膜近似；白色涂层铝 metallic=0；裸框 metallic=0.75。楼板、石材、路面及绿化按介电材料处理。

幕墙 1K Base/ORM/Emissive，UV0 图集并留边，冷暖和暗区固定；原创程序化铺装 1K、街区共享 256 px。纹理随工程打包，GLB 自包含。未使用法线图、AO 或无出处照片贴图。封闭外壳单面，冠部内缩受最小半径限制以避免翻折；斜幕墙框沿实际斜边连接，不悬空。

## 5. 预览照明与运行时昼夜

EEVEE 光线追踪、AgX；`WJ_PREVIEW_ONLY` 保存相机、太阳、面积软箱、程序天空和远景地面，导出不含它们。日景/日落/蓝调/夜景同构图，另有入口低机位、侧后方、鸟瞰、近景、全街区与动画阶段图。参数与曝光见 materials.md。

展示照明是美术方案，没有冒称特定 UTC 时刻的真实太阳。静态 GLB 自发光以标准因子和 `KHR_materials_emissive_strength` 保存；没有随机闪灯、日夜脚本时钟或拼装联动太阳。实际 Cyber-Sight 昼夜及 3600 倍时钟检查未执行，待维护者人工验收。

## 6. 部件与依赖计划

{counts['parts']} 个稳定 PART，直属固定 GEO_ROOT；每层分楼板及两侧幕墙，玻璃/框/铝带为同一运动件，SOHO 示意字样随所属幕墙移动。核心按五层一段，冠部/封顶/入口独立，场地固定。枢轴为构件中心；`parts.json` 保存 glTF 父局部装配 TRS、爆炸偏移、飞入起点、阶段、依赖和 seed。

源工程保留完整部件映射。数据审计没有未满足的到位依赖；内部结构只是可视化分解，不用于结构工程验收。

## 7. 爆炸与飞入动画参数

| 参数 | 定稿 |
| --- | --- |
| 拼装 | BUILD_ASSEMBLY，30 fps，0–900 帧，30 s |
| 空场 | 0–1 s 保留景观与街区，主体无静态副本；待机正比例 1e-4 |
| 核心 / 楼板 / 幕墙 | 约 1–5 / 3.5–20 / 8–21.3 s 错峰；单件约 0.8–1.3 s |
| 飞入路径 | 所有构件由装配点上方 225–300 m 的待机区向下进入；短侧移和克制偏航，smoothstep 到位减速 |
| 高空装配 | 部件装配终点为地面装配位置整体上移 85 m；锚点保持不动 |
| 整体落地 | 22–27 s，全部部件共同下降 85 m；27–30 s 完整保持 |
| 爆炸 | BUILD_EXPLODE，0–360 帧，12 s；1.5–8 s 分解，8–12 s 保持 |
| 爆炸方向 | 楼板逐层向上，幕墙两半外展并分层上移；具体每件位移见 parts.json |
| 导出 | 静态无 clip；两个动画各只含一个 clip，默认节点姿态均为完整成品 |
| 采样 | 源工程与 glTF 逐帧 30 fps、共同 t=0，核心 TRS，固定种子 7331 |
| 首末一致性 | 文件读取检查最大分量误差 {summary['endpoint_max_component_error']}；装配末帧/爆炸首帧与静态相同 |

已用纯函数任意进度采样检查暂停、乱序采样和重播；可见阶段截图和视频另行逐图检查。完整几何全程包围盒见 motion-audit.json；峰值 {motion['peak_moving_parts']} 件共同下降。不是刚体或无碰撞施工仿真；核心与楼板接口存在示意套接，场地保持静态。

## 8. 工程、脚本、预算与发布

`.blend`、三个主体 GLB、`scripts/`、`textures/`、参考、附录与验证都在本项目；街区单独在 `model-assets/geo-context/wangjing-soho-1500-v1`。相对路径与固定 seed 可复现。脚本只替换本项目场景/集合，不清空用户其他集合；制作在独立后台工程中完成，实况 Blender 保留原有场景。

| 文件 | bytes | 三角面 | nodes / primitives | Validator errors / warnings |
| --- | --- | --- | --- | --- |
{rows}

三塔及场地约 {counts['asset_triangles']:,} 三角面，属于大型建筑组精细档预算；动画峰值较高，未承诺设备帧率或显存。没有把动画伪装成质量版本，目录主模型为静态 GLB，街区为合法 3d-tiles resource；动画直接地址在 README。

## 9. 实际验收与交付清单

- 已完成：参考原图保存、实际脚本执行、固定地理锚点、PBR/纹理/UV 文件检查、单 clip/共同时间、向下飞入与 85 m 下降数值检查、无预览对象泄漏、Khronos 逐文件 0 错误/0 警告。
- Blender 视觉证据：预览目录保存，视觉验收细目见 verification/visual-review.md；原图版权与几何估算边界见 references/README.md。
- 发布：具体目标提交、Vercel READY、线上 HTTP/MIME/CORS/bytes/SHA-256 以 verification/deployment.json 为准，未生成该证据前不声称发布完成。
- 未执行：Cyber-Sight 前端/浏览器自动化、目标引擎视觉与设备性能验收、真实地形贴合、精密测绘对照。
'''
    (ROOT/'model-brief.md').write_text(brief,encoding='utf-8')
    readme=f'''# 望京 SOHO · 空中构筑

三座流线塔楼、连续白铝遮阳带与镀膜玻璃，配套半径 1500 米的真实轮廓街区。建筑设计：Zaha Hadid Architects / CCDI；此处为 AIModels 独立展示重建。

![日景 · Cycles](previews/beauty-day.png)

![夜景](previews/night.png)

## 交付

- [Blender 源工程](wangjing-soho.blend)：米制、打包纹理、{counts['parts']} 个运动部件、可编辑 30 fps 拼装时间轴。
- [静态 GLB](https://jt-ai-models.vercel.app/models/wangjing-soho/wangjing-soho.glb)。
- [高空飞入拼装 GLB](https://jt-ai-models.vercel.app/models/wangjing-soho/wangjing-soho-assembly.glb)：30 s；构件向下飞入，在地上 85 m 完整组装，22–27 s 整体下降，保持至 30 s。
- [爆炸分解 GLB](https://jt-ai-models.vercel.app/models/wangjing-soho/wangjing-soho-explode.glb)：12 s，分层/外展分解并保持。
- [街区 3D Tiles](https://jt-ai-models.vercel.app/model-assets/geo-context/wangjing-soho-1500-v1/tileset.json)：1463 栋建筑脚印、道路、绿地；与主体同锚点。
- [拼装预览视频](previews/assembly-preview.mp4)、[爆炸预览视频](previews/explode-preview.mp4)、[分镜与昼夜图](previews/)。视频是压缩预览，源工程与 GLB 保留完整采样。
- [任务书](model-brief.md)、[部件](parts.json)、[动画](animation.json)、[材质](materials.md)、[参考来源](references/README.md)、[验证摘要](verification/summary.json)。

目录 v1 只发现静态主模型与街区，不自动控制这两个动画。请把动画 GLB 交给支持 glTF 核心节点动画的播放器；有动画文件不等于当前 Cyber-Sight 普通模型卡已有拼装拖动面板。

## 精度与依赖

塔高 118/127/200 m 来自 ZHA/CTBUH，平面与北向来自 OSM，曲面和细节结合署名 ZHA 图纸及实景拟合。内部结构、第三低亭、场地细部为示意，非 BIM。街区只有 4 栋有源高度、58 栋按楼层估算、1411 栋按类型估算，不能当作精细测绘模型。

WGS84 116.47506° E / 39.99547° N；真实椭球高未知。目录与街区的 0 是椭球演示值。GEO_ROOT 不参与动画，glTF +X 北 / +Y 上 / +Z 东。

19 张参考原图已本地保存在 references/，版权归原作者。Git 中不再分发原图；提供下载脚本、URL、作者、哈希和用途。纹理为原创，已随 `.blend` 打包，GLB 自包含。公开源地理数据按 ODbL / CC BY 4.0 署名。

## 复现

在仓库根目录运行。Python 3.12+（此轮实际 Python 3.14.7）、Pillow、NumPy、Shapely、pyproj、mapbox-earcut；Blender 5.2.1 LTS。主构建不需要付费生成器或外部模型。

```powershell
python models/wangjing-soho/scripts/acquire.py
python tools/geo-context/fetch_context.py --config models/wangjing-soho/context-source-config.json --output models/wangjing-soho/references/overture
python models/wangjing-soho/scripts/prepare.py
blender --background --factory-startup --python models/wangjing-soho/scripts/build_model.py
python models/wangjing-soho/scripts/export_animation.py
python models/wangjing-soho/scripts/audit.py
blender --background models/wangjing-soho/wangjing-soho.blend --python models/wangjing-soho/scripts/render.py -- stills
blender --background models/wangjing-soho/wangjing-soho.blend --python models/wangjing-soho/scripts/render.py -- explode
blender --background models/wangjing-soho/wangjing-soho.blend --python models/wangjing-soho/scripts/render.py -- video
node models/wangjing-soho/scripts/validate.cjs
```

`node` 验证器依赖 `gltf-validator`；可安装到本机临时工具目录再通过 NODE_PATH 指向，避免向模型工程加入 node_modules。视频编码命令见 `scripts/encode_previews.ps1`。脚本不清空用户其他场景，重复制作只替换项目命名集合；推荐后台独立运行。

## 验证与限制

四个 GLB 的 Khronos 校验均 0 错误/0 警告。验证器仅忽略常量材质未使用 UV 的 UNUSED_OBJECT 信息，不忽略错误/警告。检查了导出 PBR、内嵌图片、单面、相机/灯排除、共同 t=0、严格递增采样时间、首末一致性、向下飞入、85 m 整体下降与保持。

Blender 图与 GLB 结构验证属于制作证据；Cyber-Sight 昼夜、实际 GPU/播放/首次 ready 和地形效果由维护者人工验收，此轮没有运行前端或浏览器自动化。
'''
    (ROOT/'README.md').write_text(readme,encoding='utf-8')
    print('Updated actual brief and delivery README')
if __name__=='__main__':main()
