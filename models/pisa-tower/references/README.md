# 保存的建模参考

采集开始2026-10-20，补充2026-10-21。`download-manifest.json`逐张记录原图URL、机构/作者、像素、字节数和SHA256。图片经过人工查看，用于形态、入口、柱头、钟室、石材及广场布置；不以历史图倾角代替修复后研究。

- `grassi-elevation-section.jpg`：Raniero Grassi历史立面与剖面，Library of Congress LCCN2003688771，公有领域/无已知出版限制，随Git保留。[原始记录](https://lccn.loc.gov/2003688771)。旧图中内部结构和倾角不是当前测绘状态。
- `restricted/tower-*.jpg`与`tower-details-*.jpg`：Opera della Primaziale Pisana实景细部，含首层入口、石材檐口、柱头、螺旋梯、空心内筒、七口钟的形态；原页同时保存。
- `restricted/full-tower-municipal.jpg`：管理方经比萨市旅游网站展示的全塔实拍，可核对整体比例、倾斜、背面和大教堂关系。
- `restricted/tower-cathedral-municipal.jpg`、`square-panorama-municipal.jpg`：市旅游网站广场与建筑组合实景。
- `restricted/overall-terredipisa.jpg`：Terre di Pisa柱廊/石材近景。
- `restricted/cathedral-*.jpg`、`baptistery-*.jpg`、`cemetery-*.jpg`：管理方主要相邻地标实拍。
- `restricted/isprs-survey-2003.pdf`：ISPRS摄影测量研究，含南北向剖面及曲率分析。[论文](https://www.isprs.org/proceedings/xxxiv/5-W12/proceedings/04.pdf)。
- `osm-context.json`与`overpass-query.txt`：固定保存的街区原始空间数据与查询；OSM快照2026-10-20T15:50:57Z，ODbL-1.0，[署名](https://www.openstreetmap.org/copyright)。原始源数据同时压缩保存在街区附件sources中。

`restricted/`仅为本地研究及用户验收保留，不随Git/Vercel分发；原图版权和其他适用权利保留。Git克隆包括公有领域图、来源清单、采集脚本和OSM快照；需原图者可在本机查看或运行scripts/acquire.py重新从原来源采集。原创PBR纹理不包含这些照片的像素。

尺寸取舍见任务书：官方58.36m含基础；本模型地面以上中心近似56.3m；采用修复后研究3.97°南倾。当前资料未提供本项目可使用的2026年全套实测CAD，柱头雕刻、内部梯、详细石块尺寸和街区建筑高度须视为比例重建/估算。
