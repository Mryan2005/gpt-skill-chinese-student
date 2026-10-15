# 中式学生：学习代理分工

## Purpose

Use four narrowly scoped learning agents to reduce missed source details and improve organization. Each agent completes one subtask. The main skill remains the only writer of the canonical Markdown source and the subject-level graph HTML.

## Shared contract

- Give every agent the same subject, source paths, current Markdown/graph paths, and batch identifier.
- Put each report in a separate path such as `<project>/.codex/learning-reports/<batch-id>/<role>.md`. Agents must not write the canonical Markdown, graph HTML, learner state, task state, or design memory directly.
- Agents may read the source materials and existing graph. In `学习`, they may use web search when needed for understanding or finding related examples, but must record source titles/URLs and what each source clarified. They must never silently convert external material into an official answer.
- Every report must label claims as `原始材料`, `外部补充`, `题目推导`, `官方解析可读部分`, or `待核实`. A report must not present an inferred or clipped continuation as original or official.
- Write prose as Markdown and formulas as delimited LaTeX. Run `scripts/validate_markup.py` on each report before the main skill reads it.
- Agents must flag anything that could later become an exam gap: missing definition, missing condition, unclear formula, unsupported example, unresolved relation, or incomplete source. Do not report a subtask as complete while hiding such a gap.
- Keep the four roles disjoint. An agent may flag a dependency for another role, but it must not perform that role's work.
- The main skill waits for all four reports, checks contradictions and source boundaries, then merges them. If one agent fails, continue with the remaining reports and mark the missing subtask instead of inventing its result.
- In `考试`, do not use this learning delegation to obtain outside knowledge. The exam still reads only the current subject graph.

## Roles

### 1. 内容提取代理

Read the supplied images or source files in order, one at a time. Return:

- the original readable text and source path/sequence;
- formulas transcribed into LaTeX with the established delimiters;
- tables, diagrams, captions, and annotations that affect meaning;
- chapter/knowledge-point guesses and exact unreadable or conflicting boundaries.

Do not summarize away the source content and do not derive the final highlights.

### 2. 内容细化代理

Read the extraction report and the source material. Turn the material into an understandable, source-grounded knowledge-content draft:

- definitions, conditions, mechanisms, procedures, examples, and boundaries;
- verified clarifications from learning-time web research when needed;
- separate labels for original course content, external clarification, and unresolved understanding.

Every sentence added from a web source or inference must stay in a labeled `外部补充` or `题目推导` block. Do not fold it into `原始材料`.

Do not split sentences into fake highlights, search for related questions, or decide graph edges.

### 3. 相关例题代理

Read the refined content and existing question sources. Find or map related questions/examples from supplied materials and, when learning requires it, reliable web sources. Return each example with:

- complete question or example text and source;
- type and tested knowledge points;
- a general solving route;
- an official answer only when the source provides or verifies one;
- a provenance state for the answer: `官方解析可读部分`, `来源未提供`, or `待核实`;
- for multiple-choice/fill-in items, a logically derived speed route, conditions, and failure boundary.

Do not invent a question, official answer, or source attribution.

### 4. 关联映射代理

Read the refined content and example report. Build the semantic map:

- canonical chapter key and stable knowledge-point ID/title;
- duplicate or same-concept matches that should share one node;
- related node IDs and the reason for every edge;
- missing prerequisites, cross-chapter dependencies, and uncertain relations.

Do not rewrite the source content or generate final highlights.

## Merge order

The main skill merges in this order:

1. Store the extraction report's original content and source markers in the same Markdown file. If the hash-table fallback is needed, put the chapter hash table at the front and detailed content after it.
2. Add the refinement report as verified explanation, conditions, and boundaries without overwriting the original content.
3. Add related questions/examples with the required question, solving idea, official answer, and tested-knowledge-point fields.
4. Add relation-map IDs and edges.
5. Read the complete merged `知识内容` and all `相关的题目`, then directly distill `从内容提取出来的重点`. Do not let any agent produce the final highlights before this merge.
6. Generate the one subject graph HTML and run the Markdown/LaTeX, source-provenance, node/edge, and rendered-view checks.

7. Run the exam-dependency gate. Mark the batch `可用于考试` only when coverage, concept clarity, question readiness, relations, notation, and provenance all pass. Otherwise mark it `学习未完成`, write the blockers to `learner_state.md` and task state, and carry them into future exams as `图谱缺口`.

If reports disagree, preserve the source conflict and mark `待核实`; do not resolve it by majority vote or by silently choosing the most convenient wording.
