# AIModels 静态发布协议 v1

AIModels 拥有模型与配套资产，Cyber-Sight 消费发布清单。继续使用 `models/`、`model-assets/`、`tools/` 分类，不改变旧定位和验收记录。

制作前按 [CS-AM-1 建模详细要求](modeling-requirements.md)交付材质、光照、定位、分件和动画。静态完整模型作为目录主模型；`variants` 只表示精细度，`resources` 仍只接受下文两种类型。2026-10-19 起通过可选 `modes` 声明飞入/爆炸文件，保留旧 v1 字段及语义。`parts.json`、`animation.json` 仍是制作附录，消费端不据此猜测文件或控制动画。

## 文件与版本

- 根 `catalog.json`：`version: 1`、`updatedAt` 和 `models`，条目含稳定 `id`、`label`、`description`、可选 `thumbnail`、`manifest` 和质量选择用的 `variants`（id、label）。
- 各项目 `model.json`：版本、稳定 ID、展示信息、主模型 `model`、质量 `variants`、`placement`、`resources`、`attribution`。
- 资源 URL 相对所在 JSON 文件解析；模型与附件必须位于同一发布源。目录不包括参考资料目录、临时文件或未发布草稿。

## 模式、精细度与默认值（兼容扩展）

顶层 `model` 为静态成品（`static`），顶层 `variants` 为静态精细度列表。可选 `modes` 最多两项，只接受 `assembly`（飞入拼装）、`explode`（爆炸分解），每项包含 `id`、可选 `label`、必需的 `model`、可选 `variants`、`defaultVariant`。各模式的 `model` 为 `{url}`，生成后与顶层主文件一样包含 `bytes/sha256`；各自的 `variants` 延续 `{id,label,url}` 形式。静态不用在 modes 中重复声明。

| 字段                          | 未声明时             | 显式声明约束                                |
| ----------------------------- | -------------------- | ------------------------------------------- |
| `modes`                       | `[]`，仅静态         | 不重复，只能是 assembly/explode             |
| 顶层或模式内 `variants`       | `[]`，仅本模式原始版 | 最多 8 项，ID 唯一，不能使用保留值 original |
| 顶层 `defaultMode`            | `static`             | 必须为 static 或已声明模式                  |
| 顶层或模式内 `defaultVariant` | `original`           | 必须为 original 或本模式已有的精细度 ID     |
| 额外模式 `label`              | 飞入拼装／爆炸分解   | 非空字符串，最多 200 字符                   |

顶层 `defaultVariant` 只控制静态；动画未声明精细度时不会继承静态精细度。`original` 总是当前模式的主文件，不表示存在更高精度。缺失字段使用默认值，`null`、非法类型、未知 ID、缺失文件或不存在的默认引用必须报错。所有文件均须进入 Git 跟踪，通过相同的文件摘要与嵌套依赖校验。示例（精细度文件必须真实存在）：

```json
{
  "model": { "url": "building.glb" },
  "variants": [{ "id": "balanced", "label": "均衡版", "url": "building-balanced.glb" }],
  "defaultMode": "static",
  "defaultVariant": "original",
  "modes": [
    {
      "id": "assembly",
      "model": { "url": "building-assembly.glb" },
      "variants": [
        { "id": "balanced", "label": "均衡版", "url": "building-assembly-balanced.glb" }
      ],
      "defaultVariant": "balanced"
    },
    { "id": "explode", "model": { "url": "building-explode.glb" } }
  ]
}
```

发布器在 `model.json` 补齐默认值、模式标签与精细度数组。`catalog.json` 保留旧 `variants`，另提供 `defaultMode/defaultVariant` 和各额外模式的 `id/label/defaultVariant/variants`（variants 仅 id/label）摘要，供加载前选择；实际文件只从 `model.json` 读取。旧 Sight 忽略新字段仍加载静态，新 Sight 将缺失声明的旧目录归一化为静态/原始版，并保留既有 variants。

Sight 切换模式时选择该模式默认精细度，点击加载/重新加载才替换整组；已加载身份包含模型 ID、模式 ID、精细度 ID。加载动画不自动播放，仍由已加载数据的动画面板控制。发布模式仅选择资产，不修改全局时钟、地形或昼夜；相机和交互效果由维护者人工验收。不兼容的协议变化仍须升级版本。

`model` 和 variants 提供 `url`、`bytes`、`sha256`，variants 另有 `id`、`label`。`placement` 提供 `crs: EPSG:4326`、`coordinateSource: manifest`、`terrain: ellipsoid | any`、经纬度、椭球高 `height`、scale、heading/pitch/roll（度）与 `notice`。`height` 不得使用建筑本身高度，演示用 0 只适用于无真实地形场景，不声称实测。

resources 提供 `id`、`label`、`kind: 3d-tiles | geojson`、`url`、`required`；3D Tiles 可显式提供 `dayNight`，只用于本仓库已制作的兼容街区。署名条目为 text、url。配套资源通过模型组加载，不提供独立地标场景入口。

面向当前 Cesium 消费端的 3D Tiles 必须设置正的、有限的顶层 `tileset.geometricError`，表示完全省略该瓦片集的误差；叶节点的 `geometricError` 可以为 0。不能把两者都设为 0，否则 Cesium 会在进入根内容前跳过遍历，HTTP 成功也不会显示几何。发布检查会拒绝顶层 0；仍需人工验证实际显示。

## 发布工作流

每个正式模型维护 `model.source.json`，填写模型文件、预览、定位来源或显式 placement、质量版本及配套资源。运行 `python tools/catalog/publish.py` 生成每模型描述和 catalog.json；`python tools/catalog/publish.py --check` 核对生成内容及已跟踪文件，验证 GLB/glTF 与 3D Tiles 的相对依赖。生成过程会计算主文件与质量版本的字节数及 SHA-256，不重写模型二进制、原始 placement 或 scene。

新增模型需加入 Git 后通过 check；参考图、Blender 源文件与脚本不作为场景资源自动加载。提交目录与发布描述，Vercel 继续静态托管。发布后验证 catalog、模型描述、模型文件及配套资源的 HTTP、类型和跨域头。

## 兼容和失败

消费端校验版本、唯一 ID、相对地址、坐标和资源类型；catalog 失败不影响手工 URL。目录加载以声明位置为准，不再重复询问 GLB 内坐标。必需资源失败整组回滚，可选配套失败保留主体并标注；取消清理本次资源，重复点击已加载项定位，整组显隐与移除。有配套的模型不能单独移动。地形不兼容先提示，不自动改变场景地形。

## 当前实施

2026-10-19：9 个主模型；国家大剧院保留 balanced/compatible 精细度，望京 SOHO 显式发布 assembly/explode 模式，各自只有原始版。其他模型未声明字段自动使用静态/原始默认。未重制二进制或伪造缺失档位。原接入证据见[交付记录](catalog-delivery.md)，本轮验证见[模式声明记录](verification/2026-10-19-model-modes.md)。
