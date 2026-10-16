# 数学 Question Bank Schema 与映射

## Question schema

```json
{
  "id": "series-mcq-12",
  "sourceId": "series-q12",
  "type": "multiple_choice",
  "originalNumber": 12,
  "stem": {
    "segments": [
      {"kind": "text", "value": "判断级数的敛散性。"},
      {"kind": "math", "mathObjectId": "q12-ratio"}
    ]
  },
  "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
  "figures": [],
  "subparts": [],
  "solution": {
    "text": "...",
    "status": "COMPLETE",
    "referencesMathObjectIds": ["q12-ratio"],
    "coreOperations": ["series_ratio_test"],
    "verifiedFragment": null
  },
  "officialAnswer": "B",
  "historicalAnswer": null,
  "derivedAnswer": "B",
  "officialSolution": null,
  "historicalSolution": null,
  "derivedSolution": {
    "text": "先计算相邻项比值。比值极限为 1，因此比值判别法失效，故选 B。",
    "origin": "AI 独立推导",
    "confidence": 0.96,
    "needsReview": false
  },
  "answerEvidence": [
    {"kind": "official_answer", "value": "B", "sourceId": "series-q12-answer"}
  ],
  "solutionEvidence": [
    {"kind": "derived_solution", "description": "AI 根据完整原题独立求解", "sourceId": "series-q12"}
  ],
  "sourceStatus": "COMPLETE",
  "questionStatus": "COMPLETE",
  "solutionStatus": "COMPLETE",
  "answerStatus": "ANSWER_VERIFIED",
  "primaryCardId": "ratio-test",
  "secondaryCardIds": ["positive-series"],
  "mappingEvidence": {
    "coreOperations": ["series_ratio_test"],
    "whyPrimary": "题目的决定性动作是计算相邻项比值并与 1 比较。",
    "whyNotOnlyChapter": "章节只说明范围，不能说明真实解题动作。"
  },
  "semanticProfile": {
    "stemConcepts": ["series", "ratio_limit"],
    "solutionConcepts": ["series", "ratio_limit"],
    "allowedDerivedConcepts": ["convergence_decision"]
  },
  "sourceIds": ["series-q12", "series-q12-answer"]
}
```

## 题目状态

- `sourceStatus`：原始材料是否已读、是否有冲突；
- `questionStatus`：题干、选项、条件、分问、图形和公式是否完整；
- `solutionStatus`：解析是否完整、是否有断句/空缺；
- `answerStatus`：答案是否有来源和是否验证。

推荐值：`COMPLETE`、`QUESTION_INCOMPLETE`、`SOLUTION_INCOMPLETE`、`DERIVED_COMPLETE`、`ANSWER_MISSING`、`ANSWER_UNVERIFIED`、`ANSWER_VERIFIED`、`DERIVED_VERIFIED`、`CONFLICTING`。不同字段可以同时处于不同状态。

真实残缺题仍然建立 Question Record。例如题 21 只拍到一半时，保留题号和已读片段，设置 `questionStatus = QUESTION_INCOMPLETE`，列出 `integrityFlags`，不要删除，也不要用章节总览补位。

## Primary Mapping Gate

每道题必须满足：

```text
primaryCardId       恰好一个、引用存在的 Card
secondaryCardIds    可为空或多个、不得包含 primary、不得重复
mappingEvidence     有真实解题动作和为什么选择 primary 的说明
```

映射顺序是：

```text
题干/条件/图形
→ 实际解题过程
→ 核心数学操作
→ primaryCardId
→ secondaryCardIds
```

不能因为题目出现在“无穷级数”章节就同时挂到该章节下所有卡。综合题可以把 Problem Pattern Card 作为 primary，但必须说明为什么不能归入一个单独基础方法。

## Question Deduplication

完整题目只保存一次。去重键按 `sourceId + originalNumber + type` 优先；来源不同或题号缺失时，再用规范化的题干/数学对象指纹进行近重复检查。重复题目报告 `QUESTION_DUPLICATED`，不能把完整题干复制到每张卡。

题组必须先拆分成独立 Question Record。题组、照片组、章节总览和题号范围不算题目；未拆分时报告 `QUESTION_GROUP_NOT_SPLIT`。

## Question Integrity Gate

选择题：题干、公式、选项数量、选项内容、必要图片都可核实；空选项报告 `EMPTY_OPTION`。

填空题：空格附近公式、条件、目标和必要图形可核实。

解答题：全部条件、全部分问、跨页连续性、图形、公式和求解目标可核实。

任一公式、矩阵、根式、上下限或选项在源中存在但记录丢失，设置 `MATH_CONTENT_LOSS`；不可读但保留来源时设置 `MATH_UNREADABLE`。不允许用空白字符串表示“已提取”。

## Solution Integrity 与 Answer Evidence

解析出现“由 ____ 得 ____”“代入 ____ 可得”或明确断页时，设置 `solutionStatus = SOLUTION_INCOMPLETE`，保留 `verifiedFragment`，不要包装为完整解析。

答案和解法证据至少区分：

```text
official_answer    题目来源或官方答案表直接提供
historical_answer  旧站/历史记录保存的答案，未必可核实
derived_answer     根据完整题干和可复算步骤推导出的答案
official_solution  来源明确的官方解析
historical_solution 历史记录中的解析，未必可核实
derived_solution   AI 根据完整原题独立生成的题目级解法
```

`historicalAnswer = "B"` 必须伴随 `answerStatus = ANSWER_UNVERIFIED`，不能自动填入 `derivedAnswer`。题目完整时可以独立生成 `derivedSolution` 和 `derivedAnswer`，但必须标记 AI 独立推导和 confidence。官方、历史和推导答案或解法冲突时报告 `ANSWER_PROVENANCE_CONFLICT`，保留各自来源。

题目关键条件、公式、选项、图形或分问缺失时，禁止生成 `derivedSolution` 或 `derivedAnswer`。原解析缺失不等于不能独立求解，题目完整性决定是否可以推导。

## Question Semantic Consistency

`semanticProfile` 是结构化的一致性证据：解析中的 `solutionConcepts` 必须来自题干概念或明确的 `allowedDerivedConcepts`；解析引用的 `mathObjectId` 必须来自该题的 stem/options/figures。题干与解析动作不一致时报告 `QUESTION_SOLUTION_MISMATCH`。primary 卡的 `operationTags` 必须与 `mappingEvidence.coreOperations` 有交集，否则报告 `QUESTION_CARD_MISMATCH`。
