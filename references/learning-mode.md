# 中式学生：学习模式

## Outcome

Create or update exactly one knowledge-network HTML file for the requested subject. One subject maps to one graph HTML file: do not split a subject into multiple graph HTML files or merge different subjects into one graph file. Every knowledge point is exactly one graph node. The file must let the learner select a node and inspect its complete evidence-backed card; the graph must make the relations between nodes visible.

If the project already has a graph format, preserve its visual language and stable IDs. Otherwise prefer a self-contained offline HTML file with inline data, styles, and scripts. If local supporting files are necessary for scale, keep them local and verify every path from the HTML entrypoint.

## Workflow

1. Establish scope and sources.

   - Identify the subject, source materials, existing graph file, and output location.
   - Read the target project's `AGENTS.md`, `.codex/task-state.md`, `learner_state.md`, and `design_memory.md` when they exist and the work is part of a maintained learning Site.
   - Treat supplied source text and supplied answer keys as evidence. If a source is incomplete, unreadable, or contradictory, preserve that boundary instead of inventing content.

2. Extract nodes and relations.

   - Use stable, semantic node IDs. Do not duplicate a concept merely because it appears in several questions; add a relation or a question mapping instead.
   - Connect nodes by actual conceptual or solving-operation dependency, not by superficial topic words or answer format.
   - Keep source question numbers and type labels. Preserve the complete question text when it is readable; keep figures or a precise figure reference when a figure is essential.

3. Build every node card with these four sections, in this order:

   1. `知识内容` - preserve the original source content, textbook content, or other supplied course content as the node's main material. Add source-grounded explanations, definitions, conditions, formulas, procedures, and boundaries when needed, but do not replace the source/course content with a summary-only rewrite.
   2. `从内容提取出来的重点` - concise, scannable points extracted from that node's `知识内容`; do not introduce unsupported claims or points that are not present in the source/course content.
   3. `相关的题目` - each mapped question must contain all four fields:
      - `题目` - the preserved stem/options/figure reference;
      - `自己的解答思路` - a complete route for solving, not just a formula or answer;
      - `官方答案` - the supplied official answer or `当前未提供官方答案。`;
      - `考到的知识点` - the node(s), conditions, and operation actually tested.
   4. `关联的知识点` - linked node titles/IDs, with edges rendered in the graph and a short reason for each relationship when the UI supports it.

   Never reduce a mapped question to only `题号 + 公式 + 答案`. If the question cannot yet be mapped, keep it in a clearly labeled unresolved queue with the reason and source reference.

4. Keep learning state separate from content.

   - Update `learner_state.md` only with evidence-backed `cannot_do`, `does_not_know`, and `understands` observations, retaining dated history and active gaps.
   - Update `design_memory.md` only when a visual, information-architecture, or interaction decision is made.
   - Update `.codex/task-state.md` immediately when sources, exclusions, mappings, wrong-question numbers, or completed work change.

5. Verify the user-visible artifact.

   - Check that every node has all four required sections, every relation points to an existing node, IDs are unique, and question mappings retain their provenance.
   - Open the HTML in a browser or equivalent renderer. Check graph interaction, card selection, search/filter behavior, long formulas, Chinese text, narrow layout, and print/readability when relevant.
   - Check browser-console errors and broken local asset paths. For mathematical content, verify that the actual rendered notation is readable, not merely that the source contains delimiters.
   - Report any source-limited or unresolved material explicitly; do not silently call an incomplete graph complete.
