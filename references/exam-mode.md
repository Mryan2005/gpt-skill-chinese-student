# Student: 考试模式

## Closed-book boundary

The subject's current knowledge-graph HTML is the only knowledge source for the initial answer pass. The question PDF supplies the questions; it does not supply the learned theory. Do not use web search, other websites, unrelated notes, hidden model knowledge, or an answer key during this pass. Reasoning may combine facts and procedures from multiple graph nodes, but every substantive premise must be traceable to a node or its mapped question evidence.

If the subject graph is missing, or a question cannot be supported by it, stop short of guessing. Mark the result as `图谱缺口`, name the missing concept/condition/procedure, and preserve the question for later learning repair.

## Workflow

1. Load the graph before answering.

   - Identify the subject and exact graph HTML. Read its node data and relevant card content, not just the visible node labels.
   - Confirm that the graph is the version intended for this exam. If multiple versions exist, use the one the user names or the project state identifies; otherwise report the ambiguity.

2. Read the exam PDF with the PDF skill.

   - Inspect every page needed to enumerate all questions in order, including options, figures, tables, formulas, instructions, and page breaks.
   - Preserve each question's original number and type. If extraction and visual rendering disagree, treat it as an evidence conflict and identify the page/question rather than silently choosing.

3. Freeze the first answer pass.

   For each question, record:

   - `题号 / 题型`
   - `题目`
   - `调用的知识点` - graph node IDs/titles only
   - `作答`
   - `解答思路` - the derivation or decision route supported by the graph
   - `证据边界` - `图谱支持` or a precise `图谱缺口`

   Do not open or use the solution/explanation PDF until this pass is complete. Numerical answers should be independently recomputed when the graph provides enough information; proof questions still need a written derivation rather than an unexplained result.

4. Compare with the supplied solution PDF after the first pass.

   - Use the PDF skill to read the complete relevant explanation pages and align them by question number.
   - Treat the supplied solution as the comparison reference, not as retroactive study material for the frozen answers.
   - Distinguish at least: missing note/content, missing condition or relation, unmastered question type/procedure, calculation or transcription error, question-reading error, and source ambiguity.
   - If the solution itself is missing, unreadable, or conflicts with the question, record that exact boundary and do not manufacture an official answer.

5. Feed the reflection back into learning.

   - For a missing concept, expand the relevant node's `知识内容` and `从内容提取出来的重点` with the supplied evidence.
   - For an unmastered operation, add or repair a `相关的题目` entry containing the full question, the student's route, the supplied official answer, and the tested knowledge points.
   - For a missing dependency, repair `关联的知识点` and the graph edge; for a missing condition, add the condition and a boundary example.
   - Preserve the original question and wrong-answer history. Do not overwrite the first attempt; append the comparison and correction.
   - Record only evidenced learner gaps or understandings in `learner_state.md`, and update `.codex/task-state.md` and `design_memory.md` only in their respective scopes.

6. Re-verify the repaired graph.

   - Check that the new question mapping and official answer point to the supplied solution evidence, all node IDs/edges remain valid, and the required four card sections remain present.
   - Render and inspect the updated HTML. Re-run relevant static checks and browser-console checks.

## Final report shape

Report the answer sheet and graph-supported boundaries, then the comparison result and the exact learning repairs. Include unresolved questions separately. Never imply that an unsupported answer is correct merely because it is plausible.
