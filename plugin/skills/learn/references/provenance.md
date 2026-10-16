# 通用证据与来源边界

## Evidence labels

每条学习内容使用下列标签之一或多个：

~~~text
原始材料
外部补充
题目推导
官方解析可读部分
待核实
~~~

不同标签不能静默合并。外部材料用于理解时，记录来源标题、URL 和它澄清的内容；它不能覆盖用户原始材料或伪造官方答案。

## Web boundary

学习阶段可以使用可靠 Web 资料理解陌生概念、条件、证明或背景。考试阶段仍然只使用当前 Subject 图谱。外部页面无法确认同一来源、版本、题号和题干时，不得恢复缺失题面。

## Persistent state

learner_state 只保存有证据的 understands、cannot_do、does_not_know 和主动缺口。task-state 保存来源、排除项、题号、映射和完成事实。design_memory 只保存视觉、信息架构和交互决定。

## Completion

任何缺失、冲突、不可读、无来源或未验证内容都进入 readiness 风险列表。不要因为文件生成、HTML 打开或静态脚本通过就报告完整。

## Derived answer and solution

原解析不存在不等于没有解法。若题目足够完整，领域模型可以生成 derived_solution 和 derived_answer，并标记 AI 独立推导、confidence 和 needs_review。若题目关键内容缺失，derived_solution 和 derived_answer 必须为空。
