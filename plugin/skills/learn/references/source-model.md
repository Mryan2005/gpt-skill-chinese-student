# 通用来源模型

## Source intake

Source Intake 将原始图片、PDF、教材、笔记、题目、解析、答案和外部补充分成可追踪的 Source Records。每条记录至少有稳定 ID、来源位置、读取状态、entityType 和 provenance。

通用 entityType：

~~~text
chapter_metadata
knowledge_content
question
solution
answer
answer_key
formula
figure
example
note
question_group
unclassified
~~~

只有 entityType 为 question 的独立来源才有资格创建 Question Record。chapter_metadata、question_group 和 unclassified 不能进入题库。

## Intake boundary

- 先清点来源，再读取内容；
- 保留文件名、页码、序号、版面和跨页关系；
- 不可读、冲突或缺页内容保留为明确状态；
- 不用章节目录、题号范围或外部网页补齐原始题目；
- 领域模型可以增加 entityType 或 MathObject，但不能绕过通用来源边界。

## Output

Source Records 进入统一 Subject。它们可以被领域 playbook 转换为数学 MathObject、语言例句或其他领域实体，但来源位置和证据状态不能丢失。
