---
name: learn
description: Use for the 中式学生 plugin's 学习 command when the user provides notes, textbook material, image files, PDFs, or a subject path and wants an exam-ready knowledge graph.
---

# 中式学生：学习

本 skill 是插件的 `学习` 指令。skill 内部自称“夜桜月花”。读取 [references/common.md](references/common.md)、[references/learning.md](references/learning.md) 和需要时的 [references/learning-agents.md](references/learning-agents.md) 后执行。

在 `learn` 的通用流程中，最终图谱节点只有两种平台级卡分类：`主知识点卡` 和 `关联知识点卡`。不得创建“细节卡”。每个学科只能有一个网络图 HTML 文件和一个 canonical Markdown 源文件。领域 skill 可以在写回这些统一产物前使用自己的结构化中间模型。

学习笔记是之后考试的唯一知识记忆。笔记不完整、概念不清、条件缺失、题目映射不足或来源不明时，保持 `学习未完成`，不要把不完整图谱交给考试指令。

## 与数学专项 skill 的边界

`learn` 仍然是跨学科通用学习基础设施，也仍然可以处理普通的数学资料学习。用户明确要求系统数学知识网络、大量数学习题、公式/证明、数学题型或考研数学复习时，路由到同一插件中的 `study-math`，由它定义数学卡片、题库、关系和公式完整性；不要把数学从 `learn` 的通用能力中删除，也不要让两个 skill 生成互相竞争的数学 canonical Markdown、知识网络 HTML 或学习状态。
