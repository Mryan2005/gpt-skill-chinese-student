# 中式学生：考试模式

## Closed-book boundary

The subject's current knowledge-graph HTML is the only knowledge source for the initial answer pass. This restriction overrides the learning mode's permission to use web research. The question PDF supplies the questions; it does not supply the learned theory. Do not use web search, other websites, unrelated notes, hidden model knowledge, or an answer key during this pass. Reasoning may combine facts and procedures from multiple graph nodes, but every substantive premise must be traceable to a node or its mapped question evidence.

If the subject graph is missing, or a question cannot be supported by it, stop short of guessing. Mark the result as `图谱缺口`, name the missing concept/condition/procedure, and preserve the question for later learning repair.

## Saved answer record

The first-pass answers must be saved to a durable local Markdown record before the explanation PDF is opened. Use the target project's existing convention when one exists; otherwise use `<subject-project>/.codex/exam-attempts/<exam-id>-attempt.md`. If there is no project directory, use `exam-attempts/<exam-id>-attempt.md` beside the subject graph HTML. Do not overwrite an existing attempt; create a new exam ID or continue the matching unfinished record.

The record must contain the exam source path/name, subject graph path/version, attempt status, and one entry per question with `题号 / 题型`, the original `题目`, `调用的知识点`, `作答`, `解答思路`, and `证据边界`. Write ordinary text as Markdown and transcribe readable mathematical expressions as LaTeX using the graph's established delimiters. Save or append the record after each question when practical, and always verify that every question has been recorded and the status is `首轮作答完成` before reading the explanation PDF.

Keep the `首轮作答` section immutable. Add later sections such as `解析对照`, `错误原因`, and `知识图谱补充` after it; never rewrite the first answers to match the explanation. When an exam task is resumed, load this record first so the review uses the actual first attempt rather than a reconstructed answer.

## Post-exam method review

The review must produce two layers of method, not just a right/wrong judgment:

- `通解` - the standard, principled solution route that can be transferred to most variants of the same question type. State the concepts, conditions, derivation or procedure, and why the route works.
- `提速解法` - only for multiple-choice and fill-in questions, derive a faster route from the `通解`. It may use a justified invariant, estimation, substitution, symmetry, range check, option verification, or another logically equivalent reduction, but never guessing, memorizing traps, pattern matching, or trial-and-error without proof.
- `适用条件与失效边界` - state when the speed method is valid, when it is not, and what to fall back to. For non-multiple-choice/non-fill-in questions, keep the complete `通解` as the primary method.

For each question reviewed after the explanation, append these method fields to the saved record when applicable. Test the `通解` against the mapped question and nearby variants or related graph questions so the result aims to solve most of the type, not only the exact original question.

## Workflow

1. Load the graph before answering.

   - Identify the subject and exact graph HTML. Read its node data and relevant card content, not just the visible node labels.
   - Confirm that the graph is the version intended for this exam. If multiple versions exist, use the one the user names or the project state identifies; otherwise report the ambiguity.

2. Read the exam PDF by calling `[@PDF](plugin://pdf@openai-primary-runtime)` / the available `pdf:pdf` skill.

   - Inspect every page needed to enumerate all questions in order, including options, figures, tables, formulas, instructions, and page breaks. Transcribe readable formulas into LaTeX in the saved record; mark unreadable formulas instead of guessing them.
   - Preserve each question's original number and type. If extraction and visual rendering disagree, treat it as an evidence conflict and identify the page/question rather than silently choosing.

3. Freeze the first answer pass.

   - Create or open the saved answer record before answering. Record each question as it is completed, preserving the first answer exactly.

   For each question, record:

   - `题号 / 题型`
   - `题目`
   - `调用的知识点` - graph node IDs/titles only
   - `作答`
   - `解答思路` - the derivation or decision route supported by the graph
   - `证据边界` - `图谱支持` or a precise `图谱缺口`

   Answer every question in order. When the graph cannot support a question, still record the question and mark the answer as `图谱缺口`; do not skip it or answer from outside knowledge.

   Do not open or use the solution/explanation PDF until this pass is complete, the saved record has every question, and its status is `首轮作答完成`. Numerical answers should be independently recomputed when the graph provides enough information; proof questions still need a written derivation rather than an unexplained result.

4. After the first pass, call `[@PDF](plugin://pdf@openai-primary-runtime)` / the available `pdf:pdf` skill again to read and compare the supplied solution/explanation PDF.

   - Append the comparison to the saved record; never replace or edit the immutable `首轮作答` section.
   - Use the PDF skill to read the complete relevant explanation pages and align them by question number.
   - Treat the supplied solution as the comparison reference, not as retroactive study material for the frozen answers.
   - For every question, classify the cause when applicable: `笔记没记全 / 知识内容缺失`, `这类题型没掌握 / 解题程序不熟`, `计算错误或抄写错误`, `看题看错 / 漏看条件 / 误解题意`, or `题面与解析存在冲突`.
   - If the solution itself is missing, unreadable, or conflicts with the question, record that exact boundary and do not manufacture an official answer.

5. Feed the reflection back into learning.

   - For `笔记没记全 / 知识内容缺失`, supplement the relevant node's `知识内容` with the supplied source or explanation evidence, then regenerate `从内容提取出来的重点` after rereading the node content and all related questions.
   - For `这类题型没掌握 / 解题程序不熟`, add or repair a `相关的题目` entry containing the full question, the student's `通解`, the supplied official answer, and the tested knowledge points; make the solving procedure explicit. For a multiple-choice or fill-in question, also record a derived `提速解法` plus its `适用条件与失效边界`.
   - For `计算错误或抄写错误`, add the verified calculation checkpoint and a clearly labeled `需要小心的地方` to the relevant node's content or highlights.
   - For `看题看错 / 漏看条件 / 误解题意`, add the missed condition, contrast, or reading checkpoint as a clearly labeled `需要小心的地方` and link it to the relevant node/question.
   - For a missing dependency, repair `关联的知识点` and the graph edge; for a missing condition, add the condition and a boundary example.
   - Preserve the original question and wrong-answer history. Do not overwrite the first attempt; append the comparison and correction.
   - Record only evidenced learner gaps or understandings in `learner_state.md`, and update `.codex/task-state.md` and `design_memory.md` only in their respective scopes.

6. Re-verify the repaired graph.

   - Check that the new question mapping and official answer point to the supplied solution evidence, all node IDs/edges remain valid, and the required four card sections remain present.
   - Render and inspect the updated HTML. Re-run relevant static checks and browser-console checks, including Markdown structure and actual LaTeX rendering.

## Final report shape

Report the saved first-pass record path, the answer sheet and graph-supported boundaries, then the comparison result and the exact learning repairs. Include unresolved questions separately. Never imply that an unsupported answer is correct merely because it is plausible.
