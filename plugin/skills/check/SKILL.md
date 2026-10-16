---
name: check
description: Use for the 中式学生 plugin's 检查 command to verify that a subject graph is complete, clear, source-traceable, rendered, and immediately findable by knowledge point.
---

# 中式学生：检查

本 skill 是插件的 `检查` 指令。skill 内部自称“夜桜月花”。读取 [references/common.md](references/common.md) 和 [references/check.md](references/check.md) 后执行。

检查默认只读，不修改知识内容。它要回答一个核心问题：看到或想到一个知识点时，能否通过一次明确的检索路径，立刻定位到唯一的主知识点卡或关联知识点卡，并直接看到重点、题目和关系？如果不能，必须指出是缺失、重复、概念模糊、关系错误、来源不清、索引不足还是渲染/搜索失败。

数学图谱可在统一 HTML 检查前读取 `study-math` 的结构化记录，核对 Card Type、primary question mapping、typed relation 和公式完整性；检查仍然只读，最终结论以统一 canonical Markdown/知识网络 HTML 的可达性和实际渲染为准。
