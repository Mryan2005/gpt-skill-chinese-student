# 中式学生插件共用规则

平台 Source/Derived Contract 见 [platform-contract.md](../../references/platform-contract.md)。

- 插件提供方是 `Mryan2005`。`中式学生`是插件显示名，`learn`、`study-math`、`exam`、`check` 是系统 skill 名。
- 普通文本使用 Markdown，公式使用带定界符的 LaTeX。运行对应 skill 的 `scripts/validate_markup.py`；裸 `\\frac`、未闭合公式和只写反斜杠不算合格。
- 所有内容带证据状态：`原始材料`、`外部补充`、`题目推导`、`官方解析可读部分`、`待核实`。不同状态不能静默合并。
- 通用 learn 不规定所有学科使用同一种卡片内部结构。领域模型负责卡片类型和正文合同；平台仍禁止无来源的隐藏碎片节点。
- 一个学科对应一个 canonical Markdown 和一个知识网络 HTML。源图片、试卷和解析文件不覆盖、不改名、不删除。
- 长期学习状态、学习完成状态、主动缺口和来源边界写入项目的持久文件，不依赖对话记忆。
