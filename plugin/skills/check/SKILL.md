---
name: check
description: Use as the read-only QA and audit front door for learning artifacts, including source integrity, knowledge structure, questions, relations, retrieval, rendering, and exam readiness.
---

# 中式学生：审计入口

check 是整个学习系统的只读 QA、Auditor 和 Test Runner。它验证 learn 构建的 Subject 和领域模型生成的 artifact，但不替用户重新学习、重映射或修复内容。

## Non-negotiables

- 默认只读，不修改 Markdown、HTML、records、learner_state 或 task-state。
- 每个结论都必须有证据路径、实体 ID、观察值和期望值。
- 每个发现都必须有 code、severity、layer 和 repairOwner。
- 区分 blocker、error、warning 和 info。
- “没有发现错误”不等于“内容正确”；未执行的检查必须明确报告。
- 通用检查机制不定义数学或其他学科的卡片正确性。领域规则来自对应 domain contract。
- 发现根因后停止在报告，不在 check 内自动修复。

读取 [check-contract.md](references/check-contract.md)、[finding-schema.md](references/finding-schema.md) 和 [severity.md](references/severity.md) 了解统一报告合同。

## Routing

| 用户目标 | Playbook |
| --- | --- |
| 范围不明确或要求全面检查 | [full-audit.md](playbooks/full-audit.md) |
| 来源、分类或 provenance 有问题 | [source-integrity.md](playbooks/source-integrity.md) |
| 知识卡、节点或层级有问题 | [knowledge-structure.md](playbooks/knowledge-structure.md) |
| 题目错挂、重复或题解不一致 | [question-integrity.md](playbooks/question-integrity.md) |
| 关系断链、无类型或方向错误 | [relation-integrity.md](playbooks/relation-integrity.md) |
| 搜索找不到知识点 | [retrieval-integrity.md](playbooks/retrieval-integrity.md) |
| 页面、公式或交互显示异常 | [rendering-integrity.md](playbooks/rendering-integrity.md) |
| 是否可以拿去复习或考试 | [readiness.md](playbooks/readiness.md) |

先按用户目标选择审计 playbook，再按 Subject 选择领域 contract。数学检查读取 study-math 的 schema、validator 和 readiness contract；check 不复制数学规则。

## Done gate

使用真实 canonical artifact、Structured Records 和实际 HTML 输出。运行相关 scripts，生成结构化 findings，汇总严重程度、未执行检查、证据路径、根因和 repairOwner。检查结束时只报告验证结果，不报告已修复内容。
