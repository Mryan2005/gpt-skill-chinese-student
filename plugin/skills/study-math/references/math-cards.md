# 数学 Card Schema 与原子性

## 通用 Card schema

数学 Card 是一个带判别字段 `type` 的结构，而不是所有学科共用的固定正文顺序：

```json
{
  "id": "ratio-test",
  "moduleId": "positive-series",
  "parentId": "positive-series",
  "type": "method",
  "title": "比值判别法",
  "recallPrompt": "什么结构优先考虑比值判别法？",
  "atomicity": {
    "coreQuestion": "如何识别并执行比值判别法？",
    "independentRecallTasks": 1,
    "splitCandidates": []
  },
  "operationTags": ["series_ratio_test", "convergence_decision"],
  "understand": "...",
  "conditions": ["..."],
  "pitfalls": ["..."],
  "recommendedQuestionIds": ["series-mcq-12"],
  "questionIds": ["series-mcq-12"],
  "sourceIds": ["series-textbook-ratio"],
  "relationIds": ["ratio-part-of-positive", "ratio-alternative-root"]
}
```

必需项：`id`、`moduleId`、`type`、`title`、`recallPrompt`、`atomicity`、`sourceIds`、`operationTags`。`questionIds` 可以为空，但不能省略；没有题目时写空数组并明确题目证据尚未提供。

可选的 `scopeConcepts` 用来记录卡片覆盖的独立概念；超过三个通常说明卡片过宽，触发 `CARD_TOO_BROAD`，应回到 module 或拆成多张卡。

## 七种 Card Type

### `definition`

回答“它是什么”：`definition`、`notation`、`domain`、`intuition`、`equivalentViews`、`contrasts`、`minimumExample`。例如函数极限应明确对象、定义域、epsilon-delta 条件和与连续性的边界。

### `theorem`

回答“使用前必须检查什么”：`preconditions`、`conclusion`、`conditionRoles`、`uses`、`failureConditions`、`misuses`。例如 Lagrange 中值定理先验证闭区间连续、开区间可导，再使用结论。

### `formula`

回答“公式是什么、什么时候成立”：`formulae`、`variables`、`conditions`、`variants`、`uses`、`omissions`。每个公式对象保留变量含义和适用条件，不能把一组题目复制进公式卡。

### `method`

回答“什么时候想到、怎么做”：`signals`、`formulae`、`steps`、`stopRule`、`alternatives`、`failureConditions`。步骤是可执行动作，不是“套公式”四个字。

### `problem-pattern`

回答“这类题第一步和分支是什么”：`recognitionSignals`、`firstStep`、`decisionTree`、`tools`、`branches`、`closingChecks`、`typicalTraps`。它教拆题，不是题目垃圾桶。

### `comparison`

回答“几个相近对象如何区分”：`compares`、`dimensions`、`conclusion`、`counterexamples`。方向性、条件差异和失效边界必须可回忆。

### `bridge`

回答“面对目标如何选择方法”：`decisionQuestion`、`branches`、`outgoingRelationIds`、`closingChecks`。Bridge 必须有真实 outgoing typed relation；没有出边就是 `EMPTY_BRIDGE`。

## Card Atomicity Gate

每张卡打开后要能直接回答：是什么、何时想到、怎么用、何时不能用、最易错点、在体系中的位置。下列情况失败：

- `atomicity.coreQuestion` 为空；
- `independentRecallTasks` 不等于 1；
- `splitCandidates` 非空却没有拆卡；
- 一个章节总览同时承载多个可独立回忆的定义/方法/题型；
- 必须浏览几十道题或多个来源才能理解卡片中心问题。

错误码分别为 `CARD_NOT_ATOMIC` 或 `CARD_TOO_BROAD`。不要用字符数截断来解决；应根据独立回忆任务拆出定义卡、方法卡、题型卡或桥梁卡。

## Card Size Gate

默认上限：

```text
coreQuestion                  = 1
核心公式/公式对象             ≤ 3
步骤                         ≤ 7
核心易错点                    ≤ 5
recommendedQuestionIds       ≤ 3
主要直接关系                 约 2–6
```

超过公式、步骤、易错点或精选题上限时报告 `CARD_TOO_LARGE`。完整题库仍可有很多题，但卡片只展示 1–3 道精选题，其余通过“查看全部相关题目（N）”进入 Question Bank。

## 推荐显示层

数学卡第一视觉层依次显示：

```text
章节/类型标识 → 标题 → Recall → 类型专属内容 → 精选典型题 → 知识关系
```

来源、原始照片、外部补充、官方答案和待核实材料放在“来源与证据”折叠区域。不要把来源列表或整批照片放在卡片正文前面。
