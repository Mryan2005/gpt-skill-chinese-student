---
name: check
description: Use as the read-only multi-agent QA and audit front door for learning artifacts, including source integrity, knowledge structure, questions, relations, retrieval, rendering, and exam readiness.
---

# 中式学生：审计入口

check 是整个学习系统的只读 QA、Auditor 和 Test Runner。它验证 learn
构建的 Subject 和领域模型生成的 artifact，但不替用户重新学习、重映射或修复内容。
它按目标路由审计 playbook；全面检查时并行运行隔离专业审计代理，最后由
Finding Merger 去重并定位根因。

## Non-negotiables

- 默认只读，不修改 Markdown、HTML、records、learner_state 或 task-state。
- 每次审计前必须删除并重建整个 .check/current workspace，确认为空后才能读取本次 canonical state。
- 每个结论都必须有证据路径、实体 ID、观察值和期望值。
- 每个发现都必须有 code、severity、rootLayer 和 repairOwner。
- 区分 blocker、error、warning 和 info。
- “没有发现错误”不等于“内容正确”；未执行的检查必须明确报告。
- 通用检查机制不定义数学或其他学科的卡片正确性。领域规则来自对应 domain contract。
- 代理只能写入自己的隔离报告；Finding Merger 只能合并报告，不能修复内容。
- 发现根因后停止在报告，不在 check 内自动修复。

读取 [audit-contract.md](references/audit-contract.md)、[check-workspace.md](references/check-workspace.md)、[finding-schema.md](references/finding-schema.md) 和 [severity.md](references/severity.md) 了解统一报告合同。

## Routing

| 用户目标 | Playbook |
| --- | --- |
| 范围不明确或要求全面检查 | [full-audit.md](playbooks/full-audit.md) |
| 来源、分类或 provenance 有问题 | [source-audit.md](playbooks/source-audit.md) |
| 知识卡、节点或层级有问题 | [structure-audit.md](playbooks/structure-audit.md) |
| 来源覆盖不完整 | [coverage-audit.md](playbooks/coverage-audit.md) |
| 卡片内容不完整或过浅 | [content-audit.md](playbooks/content-audit.md) |
| 题目错挂、重复或不完整 | [question-audit.md](playbooks/question-audit.md) |
| 答案、解法或 provenance 冲突 | [solution-audit.md](playbooks/solution-audit.md) |
| 数学语义、定理或解法有问题 | [math-audit.md](playbooks/math-audit.md) |
| LaTeX 语法或公式源文丢失 | [latex-audit.md](playbooks/latex-audit.md) |
| 关系断链、无类型或方向错误 | [relation-audit.md](playbooks/relation-audit.md) |
| 页面、公式或交互显示异常 | [rendering-audit.md](playbooks/rendering-audit.md) |
| 搜索找不到知识点 | [retrieval-audit.md](playbooks/retrieval-audit.md) |
| 是否可以拿去复习或考试 | [readiness-audit.md](playbooks/readiness-audit.md) |

先按用户目标选择审计 playbook，再按 Subject 选择领域 contract。数学检查读取
study-math 的 schema、validator 和 readiness contract；check 不复制数学规则。

专业代理：[source](agents/source-auditor.md)、[structure](agents/structure-auditor.md)、
[content](agents/content-auditor.md)、[coverage](agents/coverage-auditor.md)、
[question](agents/question-auditor.md)、[solution](agents/solution-auditor.md)、
[math](agents/math-auditor.md)、[latex](agents/latex-auditor.md)、
[relation](agents/relation-auditor.md)、[provenance](agents/provenance-auditor.md)、
[rendering](agents/rendering-auditor.md)、[retrieval](agents/retrieval-auditor.md)。
最终由 [Finding Merger](agents/finding-merger.md) 汇总。

## State machine

~~~text
NEW_CHECK_REQUEST
→ CLEANUP_PREVIOUS_CHECK_RUN
→ WORKSPACE_VERIFIED_CLEAN
→ LOAD_CURRENT_CANONICAL_STATE
→ RUN_AUDITS
→ MERGE_FINDINGS
→ WRITE_FINDINGS
→ REPORT
→ CLOSED
~~~

## Done gate

使用真实 canonical artifact、Structured Records 和实际 HTML 输出。运行
reset_check_workspace.py，确认 workspace clean，再生成结构化 findings。汇总
严重程度、执行和未执行代理、证据路径、rootLayer 和 repairOwner。最终结果只能是
PASS、PASS_WITH_WARNINGS、FAIL 或 BLOCKED。检查结束时只报告验证结果，不报告已修复内容。
