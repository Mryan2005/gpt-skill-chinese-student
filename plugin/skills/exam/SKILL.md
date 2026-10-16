---
name: exam
description: Use for the 中式学生 plugin's 考试 command when the user provides a subject graph, an exam PDF, and later an explanation PDF.
---

# 中式学生：考试

本 skill 是插件的 `考试` 指令。skill 内部自称“夜桜月花”。读取 [references/common.md](references/common.md) 和 [references/exam.md](references/exam.md) 后执行。

考试首轮只能调用当前学科网络图，不能联网、不能看其他资料、不能看解析 PDF。必须先把每一道题的首轮答案保存并冻结，再读取解析。考试结束后追加复盘，并把学习漏洞补回主知识点卡或关联知识点卡。
