# 通用题库模型

Question Bank 与 Knowledge Node 分开保存。完整题目只存一份，知识卡或节点只引用 Question ID。

## Required identity

每道题需要稳定 Question ID、来源 ID、原题号、题型、完整题干和完整性状态。选择题、填空题、解答题和证明题可以由领域模型增加专属字段。

## Required evidence

Question Record 保留题干、选项、图形、分问、解析、答案证据、sourceStatus、questionStatus、solutionStatus 和 answerStatus。题目不完整时保留记录，不用章节说明替代。

答案和解法按 provenance 分开保存：officialAnswer/officialSolution、historicalAnswer/historicalSolution、derivedAnswer/derivedSolution。题目完整时，领域模型可以根据原题独立求解；derived 内容不能冒充官方内容，也不能写回 Source。

题目关键条件、公式、选项、图形或分问缺失时，不生成 derived 结论。使用 QUESTION_INCOMPLETE、MATH_CONTENT_LOSS 或 needs-review 保留这个边界。

## Mapping boundary

learn 保证题目身份、来源和完整内容。primary card、tested concept、题型操作和领域标签由领域模型决定。题目不能因为章节归属而自动挂到所有相关节点。

## Deduplication

在写回卡片前按来源 ID、原题号、题型和规范化题干检查重复。重复题报告并保留证据，不把完整题干复制到多个节点。
