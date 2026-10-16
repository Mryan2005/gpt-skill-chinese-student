---
name: learn
description: Use as the cross-subject learning front door for new material, topic study, question-set organization, subject updates, knowledge-base repair, and exam-readiness checks. It routes domain-specific work to the appropriate subject model.
---

# 中式学生：学习入口

learn 是用户学习行为的总入口。它先理解目标，选择 playbook，再判断是否需要领域模型。用户只描述目标，不需要编排代理、schema 和 validator。

## Non-negotiables

- 一个 Subject 只有一份 canonical Markdown、一份知识网络 HTML 和一份持久化学习状态。
- Source、Knowledge Node、Question、Relation、Progress 分层保存。
- 来源先分类，再进入题库或知识图谱。未分类和不可读内容保留边界。
- 原始材料、外部补充、题目推导、官方解析可读部分和待核实内容不能静默合并。
- 领域模型拥有卡片内部结构。learn 不把所有学科强行压成同一个 Card Schema。
- 代理只能写隔离报告。主 learn skill 是统一输出的唯一合并者。
- 最终 artifact 必须经过结构、来源、Markdown/LaTeX、实际输出和考试 readiness 检查。

平台合同见 [common.md](references/common.md)、[knowledge-model.md](references/knowledge-model.md)、[question-model.md](references/question-model.md)、[provenance.md](references/provenance.md) 和 [platform-contract.md](../../references/platform-contract.md)。不要把具体学科规则扩写回入口。

## Routing

| 用户目标 | Playbook |
| --- | --- |
| 新图片、PDF、教材或笔记进入学习系统 | [ingest-material.md](playbooks/ingest-material.md) |
| 系统学习一个章节或主题 | [learn-topic.md](playbooks/learn-topic.md) |
| 整理一组题目或题目照片 | [organize-questions.md](playbooks/organize-questions.md) |
| 向已有 Subject 加入新材料 | [update-existing-subject.md](playbooks/update-existing-subject.md) |
| 修复混乱、重复或不可达的知识库 | [repair-knowledge-base.md](playbooks/repair-knowledge-base.md) |
| 检查是否可以用于考试 | [validate-readiness.md](playbooks/validate-readiness.md) |

先按用户目标选择 playbook，再按 Subject 选择领域模型。数学任务读取 study-math 的数学合同；政治任务读取 study-politics 的政治合同。learn 不复制数学或政治的卡片、措辞、公式或题型规则。未来其他学科可以接入自己的领域模型。

## Shared contract

1. 读取目标项目的 AGENTS.md、.codex/task-state.md、learner_state.md 和 design_memory.md（存在时）。
2. 保持同一份 Subject 记录和统一输出。领域中间层不能成为第二份学科真相。
3. 复杂批次读取 [agent-contract.md](references/agent-contract.md)，把每个代理报告保存到隔离目录。
4. 只在当前 playbook 需要时读取 source-model.md、knowledge-model.md、question-model.md、provenance.md 或领域 skill 的 references。
5. 学习状态写入持久文件，不依赖对话记忆。来源、排除项、映射和完成状态变化及时写入 task-state。

## Done gate

运行当前 playbook 和领域模型要求的 validator。至少检查 source coverage、entity classification、stable IDs、question mappings、relations、provenance、Markdown/LaTeX 和真实输出。任一核心 Gate 失败时报告 学习未完成，列出具体缺口，并把缺口传给 exam。只有真实 artifact 和必要 Gate 全部通过时，才能报告 可用于考试。
