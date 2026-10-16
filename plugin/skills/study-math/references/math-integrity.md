# 数学完整性与 Exam Readiness Gate

## Gate 清单

数学专项完成状态只有在以下门全部通过后才可为 `可用于考试`：

1. **Source Classification**：所有来源有 `entityType`；metadata、question group、unclassified 没有漏进 Question Bank；
2. **Card Atomicity/Size**：每张卡恰好一个主动回忆核心问题，没有章节巨型卡；
3. **Question Identity**：题目 ID 唯一、题号/题型/来源稳定，题组已拆分，残缺真实题没有被删除；
4. **Primary Mapping**：每题恰好一个 primary card，secondary tags 不重复，映射理由来自真实解题动作；
5. **Question Integrity**：题干、选项、条件、图形、分问和求解目标的缺口都有状态；
6. **Solution Integrity**：解析完整性和可读片段边界明确；
7. **Answer Evidence**：官方、历史、推导答案分开，来源冲突不被静默解决；
8. **Formula Integrity**：分式、根式、矩阵、上下限、上下标、分段函数和 MathJax/KaTeX 公式不丢失；
9. **Semantic Consistency**：题干、解析、答案、primary card 和 secondary tags 不矛盾；
10. **Typed Relations**：关系有类型、方向和 why，Bridge 有出边且无断链；
11. **Recall Readiness**：每张卡有 recall prompt，类型专属字段足够支持主动回忆；
12. **Rendered Output**：canonical Markdown、HTML、公式、搜索和卡片入口已实际检查；
13. **Progress Separation**：`knowledgeMastery` 与 `questionMastery` 独立保存，主动缺口进入统一 learner state。

任一门失败：

```text
learningStatus = 学习未完成
exam boundary = 图谱缺口
```

不能因为 `validate_math.py` 通过或 HTML 能打开就报告完成。

## 错误码

结构化 validator 至少实现并输出下列错误码：

```text
CARD_NOT_ATOMIC
CARD_TOO_BROAD
CARD_TOO_LARGE
META_AS_QUESTION
QUESTION_ID_MISSING
QUESTION_ID_DUPLICATE
QUESTION_IDENTITY_MISMATCH
QUESTION_GROUP_NOT_SPLIT
QUESTION_DUPLICATED
QUESTION_WITHOUT_PRIMARY_CARD
QUESTION_MULTIPLE_PRIMARY_CARDS
QUESTION_INCOMPLETE
SOURCE_INCOMPLETE
QUESTION_SOLUTION_MISMATCH
QUESTION_ANSWER_MISMATCH
QUESTION_CARD_MISMATCH
MATH_UNREADABLE
MATH_CONTENT_LOSS
EMPTY_OPTION
SOLUTION_INCOMPLETE
ANSWER_MISSING
ANSWER_UNVERIFIED
ANSWER_PROVENANCE_CONFLICT
DERIVED_ANSWER_FORBIDDEN
DERIVED_SOLUTION_FORBIDDEN
DERIVED_PROVENANCE_MISSING
RELATION_MISSING_TYPE
RELATION_MISSING_REASON
INVALID_RELATION_DIRECTION
EMPTY_BRIDGE
DOMAIN_TEMPLATE_MISMATCH
SOURCE_METADATA_IN_QUESTION_BANK
SOURCE_UNCLASSIFIED
LEARNING_STATUS_MISMATCH
```

## 质量指标

validator 输出可复算指标：

```text
atomic_card_rate
question_primary_mapping_rate
question_duplicate_rate
metadata_leakage_rate
typed_relation_rate
relation_reason_coverage
question_semantic_validation_rate
math_integrity_pass_rate
card_size_violation_rate
```

目标：metadata leakage、multiple primary card 和完整题重复存储为 0；typed relation 和 reason coverage 为 100%。任何被状态标记的残缺题不算“完整题通过”，但也不从计数中删除。

## Knowledge/Question Mastery

统一 progress 结构至少包含：

```json
{
  "knowledgeMastery": {"knownCardIds": [], "reviewCardIds": [], "unknownCardIds": []},
  "questionMastery": {"solvedQuestionIds": [], "reviewQuestionIds": [], "unseenQuestionIds": []}
}
```

`knownCardIds` 不能由 `solvedQuestionIds` 自动推导；一道题做对也不能替代对卡片定义、条件、边界和方法选择的主动回忆。
