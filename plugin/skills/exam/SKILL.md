---
name: exam
description: Use as the closed-book assessment runner for a frozen Subject snapshot. It records first-pass answers, releases solutions only after freezing, grades performance, and produces learning-gap reports without modifying the learning artifact.
---

# 中式学生：考试入口

exam 是 Assessment / Evaluation Runner。它测量冻结知识状态下的学习表现，不负责构建知识、不定义领域卡片，也不审计 Subject 质量。

## Non-negotiables

- 开始测量前冻结 Subject snapshot。
- 每场新考试开始前必须删除并重建整个 .exam/current workspace，确认为空后才能加载新试卷。
- 考试和解析 PDF 必须由当前 AI 直接读取原始 PDF。禁止 OCR、OCR 包、外部 OCR API、转写替代输入和委托 OCR。
- FIRST_PASS 只能访问冻结的知识图谱和题目。
- 首轮禁止 Web、解析、答案表、其他资料和未冻结的新知识。
- 首轮答案必须先保存并冻结，之后只能追加 revision，不能覆盖。
- 解析释放、评分和复盘发生在答案冻结之后。
- exam 不调用 learn 或 study-math 修改被测 artifact。
- exam 输出 Exam Result、Learning Gap Report 和 Repair Requests，由 learn 或领域模型决定如何修复。

完整状态和记录合同见 [exam-contract.md](references/exam-contract.md)、[exam-workspace.md](references/exam-workspace.md)、[pdf-reading.md](references/pdf-reading.md)、[answer-record.md](references/answer-record.md)、[grading.md](references/grading.md) 和 [error-taxonomy.md](references/error-taxonomy.md)。

## State machine

~~~text
NEW_EXAM_REQUEST
  ↓
CLEANUP_PREVIOUS_RUN
  ↓
WORKSPACE_VERIFIED_CLEAN
  ↓
LOAD_EXAM_PDF
  ↓
SNAPSHOT_FROZEN
  ↓
FIRST_PASS
  ↓
ANSWERS_FROZEN
  ↓
SOLUTION_RELEASED
  ↓
GRADING
  ↓
POSTMORTEM
  ↓
CLOSED
~~~

状态只能前进。任何回退或首轮答案覆盖都生成结构错误。

## Routing

| 用户目标 | Playbook |
| --- | --- |
| 开始并完成一套闭卷考试 | [run-exam.md](playbooks/run-exam.md) |
| 已有冻结答案，读取解析并评分 | [grade-exam.md](playbooks/grade-exam.md) |
| 生成错误分类和学习缺口 | [analyze-errors.md](playbooks/analyze-errors.md) |
| 按历史记录重放一次考试或错误 | [replay-errors.md](playbooks/replay-errors.md) |

## Done gate

运行 validate_exam_record.py，确认 snapshot、状态、首轮答案、解析释放、评分和 findings 结构完整。报告 Performance、Knowledge Coverage、Graph Effectiveness、Error Profile 和 Repair Requests。考试结束后只交付结果，不直接写回 learn 或领域模型。
