# 中国诸子学术通史研究 Skill

**Zhuzi Academic History — a provenance-first research skill**

以文献考证为基础研究历代学者如何整理、解释、批评和传播诸子文献，支持著述考辨、注释比较、争议梳理、学术承变和通史写作。

本项目从方勇《庄子学史》的研究案例归纳可执行流程；可迁移的是研究方法，庄学案例不能直接充当名家、墨家等领域的史实依据。

## 内容

- 研究 Skill：七步研究流程与文献、学术史、通史写作协议。
- 30 张方法卡、64 条摘要性论断、83 条关系、9 个争议案。
- 精选论断涉及42个证据页定位，不含页文或影图。
- Python 标准库实现的 SQLite 检索、事务导入、校验、导出及离线导航。

**公开版不包含四册全文 OCR、扫描页、原始 PDF 或个人配置。本地完整资料包不是本仓库的一部分。** 详情见 [公开数据范围](PUBLIC_DATA.md)。

## 安装为 Skill

```sh
git clone https://github.com/sanmo4749/zhuzi-academic-history.git .agents/skills/zhuzi-academic-history
```

将整个仓库作为 `zhuzi-academic-history` 文件夹放入项目的 `.agents/skills/`，或个人技能目录。`SKILL.md` 位于仓库根目录；不要只复制入口文件。

在支持本 Skill 格式的工具中使用：

```text
$zhuzi-academic-history 请研究严复《庄子评点》的成书问题，区分纪年材料与作者推断，列出需要回查的原典。
```

## 本地运行

需要 Python 3.10+，无第三方依赖。在仓库根目录执行：

```sh
python scripts/init_library.py
python scripts/kb.py validate
python scripts/kb.py search 严复 --layer claims --checked-only
python scripts/kb.py entity 郭象
python scripts/kb.py disputes
python scripts/refresh.py
```

最后一步生成 `研究导航.html`，用浏览器打开即可查看关系与出处。首次初始化不会覆盖已有数据库。公开示例页文为空，所以逐页全文检索应在接入自有资料后使用。

命令行 `--root` 应放在子命令之前。可用仓库根目录的 `library.json`（不提交）指向个人资料包，格式为 `{"root":"YOUR_LIBRARY_DIRECTORY"}`；初始化脚本始终在本仓库创建示例库。

## 继续积累

先备份数据库，再执行 `python scripts/kb.py import-json 新增记录.json`；成功后运行 `python scripts/refresh.py`。新增ID不可覆盖旧记录，修订使用 `supersedes` 保存链条。接口校验不能替代研究者实际核验。字段见 [schema.sql](schema.sql) 及 [资料库协议](references/knowledge.md)。

例如向其他诸子研究迁移：

```text
$zhuzi-academic-history 为明清《公孙龙子》研究史建立文献底账，先盘点材料缺口，再提出研究提纲，不以庄学人物替代名家史实。
```

## 学术边界

`source_passage_checked` 是整理者对现代著作源段的本地核查记录；仓库没有提供可供公众对影的书页。它不等于古籍原典已核。本公开示例的独立原典核验数为0。实际写作须重新核对版本、印页、PDF页序及引文文层，并保留“可能”等判断性质。

## 许可与贡献

原创代码、研究协议和原创整理文字采用 [MIT License](LICENSE)。方勇及所引古籍、注本和现代研究的权利不因本仓库许可而转移；相关作者和文献归属继续保留，见 [来源与内容说明](NOTICE.md)。

欢迎补充方法、修正出处和改进工具。提交史实更正时，请同时给出提出者、文献版本、印页、PDF页序及核验范围；不要提交未经授权的书籍全文或个人资料。
