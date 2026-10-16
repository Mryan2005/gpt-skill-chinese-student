# 数学学习原则

这些原则约束所有 study-math playbook。它们不是某个主题的操作步骤。重复出现的错误应进入 schema、validator 或记录状态，而不是继续增加入口提示词。

## Model Mathematical Knowledge

把数学领域编码成结构：

~~~text
MODULES
CARDS
QUESTIONS
RELATIONS
SOURCES
PROGRESS
~~~

不要把 Markdown、正则和分散的 if/else 当作数据库。不要让一个通用 Card Schema 抹平 definition、theorem、formula、method、problem-pattern、comparison 和 bridge 的差异。

## Classify before mapping

Source Intake 先判断 entityType，再决定它有没有资格进入 Question Bank。chapter_metadata、question_group 和 unclassified 不能成为 question。不要在渲染阶段过滤已经错误进入题库的记录。

## Fix the first wrong boundary

追踪错误第一次发生的位置：

- 章节总览冒充题目，修 Source Classification；
- 公式变成空白，修 MathObject intake；
- 题目挂错卡，修 mappingEvidence；
- 无类型关系，修 Relation record；
- 巨型卡，修 Card Atomicity。

不要在 HTML 渲染层添加补丁来掩盖结构化记录错误。

## Preserve evidence boundaries

原始材料、外部补充、题目推导、官方解析可读部分和待核实内容不能静默合并。残缺题要保留，历史答案不能自动变成 derived answer，解析截断不能包装成完整解析。

## One canonical subject

study-math 可以使用 math-records.json 作为中间层，但只能写回当前学科的 canonical Markdown、知识网络 HTML 和 learner_state。不要创建与 learn、exam 或 check 竞争的数学库。

## User describes goals

用户说主题、材料、题组、修复目标或考试检查目标。playbook 负责选择代理、加载 references、运行 validators 和输出结果。不要要求用户手动排列内部步骤。

## Prove the artifact

结构检查、Markdown 检查和真实 HTML/console 检查分别报告。代码或 schema 通过不等于数学图谱可以用于考试。任何未验证的部分都明确标为未验证。
