# 资料库协议

## 定位与使用

公开版提供 `data/public_seed.json`、方法卡与出处定位；先运行 `scripts/init_library.py` 创建本地数据库。个人完整库可另接入逐页OCR和证据图。主入口 `研究导航.html` 可离线搜索；命令行可作精确回查。均不需要连接外部研究系统。

```powershell
python scripts/kb.py status
python scripts/kb.py search "严复" --layer claims
python scripts/kb.py search "校勘" --layer pages --limit 15
python scripts/kb.py page ZY3 316
python scripts/kb.py entity "郭象"
python scripts/kb.py disputes
python scripts/kb.py validate
```

脚本参数 `--root` 放在子命令之前。仅需Python标准库；重新OCR或渲染时按实际环境另配PDF/OCR依赖。

## 证据层级

`machine`：机器OCR或抽取，不能直接引为定本。
`text_checked`：已阅读相应OCR段落，尚未对影。
`source_passage_checked`：对应论断段落已对照现代著作影页；不代表该页全文校订，也不代表原典已核。
`primary_checked`：已实际核验所引原典，须另列原典见证与核验记录。本版未使用此状态。
`rejected`：错误记录留档，不进入研究答案。

核验状态与历史判断分开：某一“可能”推断的源段核验通过，仍然只是论者提出的可能。

## 数据模型与更新

sources固定文件SHA256；pages保存逐页原始文本及来源；entities保存有类型的名称，机器抽出的书题是 `title_label`，不能当作已辨明的作品；mentions记录页面出现；claims记录提出者、概述、认识状态、原典核验状态；evidence连接论断与页；relations仅表达特定论断所主张的关系；disputes连各说及待核事项；methods连接实际案例与操作。

本包不会自动把书名提及提升为著者关系，也不会把旧版与增补版的重复论述当作独立证据。

扩充：将含 `sources/pages/entities/mentions/claims/evidence/relations/disputes/methods` 中任意若干表的JSON交给 `kb.py import-json 文件`。按来源、页、实体、提及、论断、证据、关系、争议、方法的顺序，在事务内验证外键、页序、状态和引证范围；失败回滚。未知表或字段也会拒绝。新增ID不可覆盖已有记录；修正另建ID，并用 `supersedes` 标明前记录与修订理由。新增古籍见证须单列来源与页，并将 sources.kind 设为 `primary_source`；只有链接到实际核验过的原典证据，才可使用 `primary_checked`。不可将新文件冒充既有来源。

SQLite是更新后的主数据。导入前备份数据库；导入成功后执行 `python scripts/refresh.py`（或 `--root 资料包目录`），同步JSONL、逐页语料、统计、覆盖表和离线导航。该操作不会重建或清空数据库。核验影页图片仍需按 `来源ID_页序.png` 或 `.jpg` 存入 evidence/；文本导入不等于图片已保存。来源ID只使用字母、数字、下划线和连字符。

导出 `kb.py export-json 输出.json` 包含全部十张表，保留ID、逐页文本、论断和出处，可作为外部研究系统的数据交换层。完整导出适合备份或导入空库；向当前库重复导入会因ID重复回滚。实际服务接入、账户配置及发布不在本包内。

## 引用

推荐格式：方勇《庄子学史》第三册，正文印页308，PDF第316页，论断C…；此处为方勇推断，所涉严复序与年谱尚未独立回查。仅有OCR定位时明示“待核”，不能补造缺失的出版信息。
