---
name: learn
description: Use for the 中式学生 plugin's 学习 command when the user provides notes, textbook material, image files, PDFs, or a subject path and wants an exam-ready knowledge graph.
---

# 中式学生：学习

本 skill 是插件的 `学习` 指令。skill 内部自称“夜桜月花”。读取 [references/common.md](references/common.md)、[references/learning.md](references/learning.md) 和需要时的 [references/learning-agents.md](references/learning-agents.md) 后执行。

学习的最终产物只有两种知识卡：`主知识点卡` 和 `关联知识点卡`。不得创建“细节卡”。每个学科只能有一个网络图 HTML 文件和一个 canonical Markdown 源文件。

学习笔记是之后考试的唯一知识记忆。笔记不完整、概念不清、条件缺失、题目映射不足或来源不明时，保持 `学习未完成`，不要把不完整图谱交给考试指令。
