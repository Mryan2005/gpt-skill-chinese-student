# 数学知识层级与来源结构

## Module 与 Card 的区别

`module` 是课程骨架和导航层，`card` 是可以独立主动回忆的知识任务。下列内容默认只能是 module/metadata：

```text
函数与极限、导数与微分、积分、微分方程、无穷级数、概率论、线性代数、章节目录、章节总览、考点列表
```

示例层级：

```text
数学一
├─ 高等数学
│  └─ 无穷级数
│     └─ 正项级数
│        └─ 比值判别法
├─ 线性代数
└─ 概率论与数理统计
```

`parentId` 表示导航层级；跨层的方法选择、前置条件和替代方案写进 typed `relations`，不要把所有关系塞进层级树。

## Module schema

```json
{
  "id": "series",
  "parentId": "calculus",
  "kind": "chapter",
  "title": "无穷级数",
  "aliases": ["级数"],
  "order": 7,
  "sourceIds": ["series-overview"],
  "status": "COMPLETE"
}
```

`kind` 可为 `subject`、`course`、`chapter`、`section`、`topic`。Module 不进入 `questions` 数组，除非有独立的真实题目来源。

## Source Classification Gate

`Source.entityType` 使用下列枚举：

```text
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
```

分类规则：

| 来源内容 | entityType | 是否可进入 Question Bank |
| --- | --- | --- |
| 章节标题、目录、章节总览、知识列表 | `chapter_metadata` | 否 |
| 教材概念、定理说明、证明背景 | `knowledge_content` | 否 |
| 有题号、题干、选项/分问/求解目标的独立题目 | `question` | 是 |
| 解析步骤或解答页 | `solution` | 否，作为解析来源 |
| 答案表或单独答案 | `answer`/`answer_key` | 否，作为答案证据 |
| 一组尚未拆分的题目照片 | `question_group` | 否，必须拆分 |
| 无法判断的材料 | `unclassified` | 否，进入待核实队列 |

`question_group` 是 intake 中间状态，不是题目。拆分后每一道题拥有自己的 `question` Source 和 Question ID。章节总览的题号范围不能用来补齐缺失题目。

## Source schema

```json
{
  "id": "series-photo-overview",
  "entityType": "chapter_metadata",
  "title": "无穷级数章节总览",
  "locator": {"path": "数学一/级数/overview-01.png", "page": 1},
  "status": "COMPLETE",
  "provenance": {"kind": "原始材料", "description": "用户提供的章节照片"},
  "content": "章节目录与考点范围",
  "mathObjects": [],
  "expectedQuestions": []
}
```

Source 的 `status` 只能描述来源本身的读取状态；它不能替代题目的 `questionStatus`、解析的 `solutionStatus` 或答案的 `answerStatus`。

## MathObject：公式是结构

公式、矩阵、分段函数、积分上下限、根号范围和图形登记在 `mathObjects` 或题目片段中：

```json
{
  "id": "q12-ratio",
  "kind": "formula",
  "latex": "\\frac{u_{n+1}}{u_n}",
  "structure": {"numerator": "u_{n+1}", "denominator": "u_n"},
  "status": "VERIFIED",
  "sourceId": "series-q12",
  "locator": "题干第 2 行"
}
```

可用 `kind`：`formula`、`fraction`、`root`、`matrix`、`piecewise`、`limit`、`integral`、`sum`、`differential_equation`、`figure`。`status` 至少支持 `VERIFIED`、`UNREADABLE`、`LOST`、`CONFLICTING`。

如果源资料有 MathObject 而输出题目缺少对应对象，标记 `MATH_CONTENT_LOSS`；如果 MathObject 不可读，保留它并标记 `MATH_UNREADABLE`，不得输出空白来假装完整。

## Source Intake 禁止事项

- 不把章节总览先放入 `examples` 再等待渲染过滤；
- 不用章节归属推导题目考点；
- 不删除残缺但真实存在的题目；
- 不用外部网页内容覆盖原始题面；
- 不把一组照片作为一个“题目”挂到多个卡上；
- 不把 Markdown 标题数量当作卡片数量。
