# Beambox 知识库数据目录

- `beambox_knowledge.sqlite3`：Agent 使用的结构化本地知识库。
- `beambox_knowledge.md`：从数据库导出的可阅读资料目录与摘要。

构建或更新：

```powershell
beambox-kb build
```

只更新官网精选资料：

```powershell
beambox-kb crawl-official
```

本地检索：

```powershell
beambox-kb search "融资和资金用途"
```

数据库保存公开网页正文或搜索摘要。`status=full_text` 表示成功读取正文；
`status=search_snippet` 表示页面无法读取，只能作为低权重线索，不能当作完整原文。
`source_type=品牌官网（企业自述）` 表示来自 `beambox.com.cn`：适合确认产品功能，
但营销性、获奖和市场地位等说法仍应使用独立来源交叉验证。
