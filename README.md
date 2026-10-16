# 中式学生

chinese-student 是一个面向本地学习资料的 Agent Plugin。它把教材、图片、试卷和解析整理为可追溯的学科知识图谱，并保留足够的证据边界，供后续闭卷考试和考前检索使用。

本仓库包含插件源文件、数学专项学习模型、结构化记录 schema 和可重复运行的校验器。它不是某个具体学科的学习资料库，也不会把用户的原始图片或试卷上传到仓库。

## 四个 skill

| Skill | 用途 |
| --- | --- |
| learn | 通用学习流程。整理任意学科的来源、知识卡、关系、canonical Markdown 和知识网络 HTML。 |
| study-math | 数学专项流程。支持数学卡片类型、结构化题库、公式完整性、数学关系和考试可用性闸门。 |
| exam | 只调用当前学科知识图谱完成闭卷首轮作答，并在读取解析后追加复盘。 |
| check | 只读检查知识点是否能通过一次明确检索定位到唯一卡片，并检查来源、关系和渲染边界。 |

learn 是跨学科平台，不是“非数学 skill”。普通数学资料仍可使用 learn。当任务需要系统数学网络、大量数学习题、公式与证明、数学题型或考研数学复习时，使用 study-math。

## 设计边界

learn 统一平台能力：

~~~text
Source / Provenance
Knowledge Graph
Question Bank 基础能力
Progress
Search
Canonical Markdown
HTML / Site 输出
通用学习状态
~~~

study-math 定义数学认知结构：

~~~text
数学卡片
数学知识层级
数学语义关系
数学题目与解题动作
公式和 MathObject 完整性
答案证据
主动回忆
Math Exam Readiness
~~~

两个 skill 写回同一学科的 canonical Markdown、知识网络 HTML 和 learner_state。study-math 的 math-records.json 是结构化中间层，不是第二份数学真相。

## 数学专项模型

study-math 支持七种 Card Type：

~~~text
definition
theorem
formula
method
problem-pattern
comparison
bridge
~~~

每张卡必须有一个 recallPrompt 和一个原子化的 atomicity.coreQuestion。章节总览属于 module/metadata，不会自动成为一张巨型复习卡。

Question Bank 与知识卡分离。每道题只有一个 primaryCardId，其他卡只能通过 secondaryCardIds 引用。题目、解析、答案和来源分别保存状态，公式丢失、解析截断和历史答案不会被静默包装成完整内容。

## 目录

~~~text
plugin/
├─ plugin.json
└─ skills/
   ├─ learn/
   ├─ study-math/
   │  ├─ SKILL.md
   │  ├─ agents/openai.yaml
   │  ├─ schemas/math-record.schema.json
   │  ├─ references/
   │  ├─ examples/math-records.json
   │  └─ scripts/
   ├─ exam/
   └─ check/
tests/
└─ test_validate_math.py
~~~

## 本地验证

在仓库根目录运行：

~~~powershell
python -X utf8 plugin/skills/study-math/scripts/validate_math.py plugin/skills/study-math/examples/math-records.json

python -X utf8 plugin/skills/study-math/scripts/validate_math_cards.py plugin/skills/study-math/examples/math-records.json --require-type definition --require-type theorem --require-type formula --require-type method --require-type problem-pattern --require-type comparison --require-type bridge

python -X utf8 plugin/skills/study-math/scripts/validate_markup.py plugin/skills/study-math

python -X utf8 -m unittest discover -s tests -v
~~~

validate_math.py 检查结构化记录和数学考试闸门。validate_math_cards.py 聚焦 Card Atomicity、Card Size 和类型字段。validate_markup.py 检查 Markdown 数学定界符和裸 LaTeX 命令。实际 HTML 页面仍需在具体 Site 输出生成后检查公式、搜索、卡片点击和浏览器 console。

## 证据规则

学习内容必须区分：

~~~text
原始材料
外部补充
题目推导
官方解析可读部分
待核实
~~~

外部网页只能帮助理解定义、条件、证明或背景，不能偷偷修补原始题面，也不能把推导答案写成官方答案。源资料不完整时保留 Question Record，并设置明确的 questionStatus、solutionStatus 或 answerStatus。

## 贡献与授权

本仓库不是开放源码项目。未经版权所有者事先书面许可，不得复制、修改、分发、再许可、商业使用、训练模型或将本仓库内容打包到其他插件中。详见 LICENSE。

## 版权

Copyright (c) 2026 YAN ZHIZHONG. All rights reserved.
