# 中式学生：学习模式

## Outcome

Create or update exactly one knowledge-network HTML file for the requested subject. One subject maps to one graph HTML file: do not split a subject into multiple graph HTML files or merge different subjects into one graph file. Every knowledge point is exactly one graph node. The file must let the learner select a node and inspect its complete evidence-backed card; the graph must make the relations between nodes visible.

If the project already has a graph format, preserve its visual language and stable IDs. Otherwise prefer a self-contained offline HTML file with inline data, styles, and scripts. If local supporting files are necessary for scale, keep them local and verify every path from the HTML entrypoint.

## Understand unfamiliar knowledge before encoding

Learning is not limited to copying the supplied material. When a concept, term, historical background, formula, diagram, or question operation is new or not yet understood well enough to explain, use web search to investigate it before finalizing the node. Prefer authoritative or primary educational sources, compare sources when the meaning is ambiguous, and do not silently choose between conflicting explanations.

- Use the external material to understand and verify the concept, conditions, boundaries, and examples; do not paste it blindly or let it replace the user's original/course content.
- Record the external source title and URL, plus the point it clarified, in the same Markdown source or the node's provenance metadata. Keep the original image/text source distinguishable from supplemental web understanding.
- Put web-derived clarification in a visibly labeled `补充理解` or `外部补充` block with its source. Never merge an externally supplied sentence into the `原始材料` block without a provenance label.
- Use Markdown for prose, headings, lists, tables, and links. Transcribe readable mathematical expressions into LaTeX using the existing renderer's consistent inline/block delimiters; do not leave a formula as a plain-text approximation. If the formula is not readable, preserve the source reference and mark it as `图片内容无法核实`.
- After the concept is understood, incorporate only the verified clarification needed for the node's `知识内容`, then read the related questions before deriving `从内容提取出来的重点`.
- If reliable understanding cannot be established, mark the exact `理解边界` or `待核实` point instead of presenting an uncertain explanation as fact.

## Delegated learning pass

For a batch with multiple images, chapters, unfamiliar concepts, or many related questions, read [references/learning-agents.md](learning-agents.md) and run the four-role learning pass before merging the canonical Markdown. A small one-image task may stay inline.

## Image-to-Markdown intake

Use this workflow when the user gives an image path or a folder containing learning images. The Markdown file is the durable source for the later subject graph; do not create one Markdown file per image.

1. Resolve the input and output.

   - Accept a single image file or a folder. Inventory supported image files in a deterministic order, preferring page numbers or natural filename order; if the order is ambiguous, report the assumption.
   - Use the user-specified Markdown path when provided. Otherwise use the existing canonical subject Markdown file; if none exists, create one stable `<subject>-learning.md` in the subject project.
   - Maintain a small processing manifest in that same Markdown file, recording each image's sequence, source path, and status so that no image is silently skipped.

2. Read images sequentially.

   - Open and inspect only the current image before moving to the next one, using `view_image` or an equivalent local image-inspection tool. Read the whole image, including headings, body text, formulas, tables, diagrams, annotations, and captions; use visual inspection for layout-dependent material instead of trusting OCR alone.
   - Preserve the readable source/course content faithfully in the Markdown file. Use Markdown for text and transcribe readable formulas into LaTeX with the project's established delimiters. Keep the image path and sequence beside the captured material. If text, formula, or diagram content is unreadable, mark the exact boundary as `图片内容无法核实` rather than inventing it.
   - Save the Markdown file after each image when practical. A later image must not erase or rewrite the earlier image's captured content.

3. Place material by knowledge point.

   - Match an image's material to an existing knowledge-point heading only when the concept and meaning match, not merely because a keyword is shared. Insert the new material inside or immediately beside that existing section, keeping related explanations and examples close together.
   - If the same knowledge point appears again, extend the existing section and retain a separate source marker for the new image; do not create a duplicate knowledge-point section.
   - If no existing knowledge point can be identified confidently, append the material to the end of the same Markdown file under a clearly marked `待归类内容` section. Do not force an uncertain merge.
   - Preserve image order in the source markers even when the material is merged into an earlier knowledge-point section. This keeps both conceptual proximity and a recoverable source trail.

### Hash-table fallback

If heading-based insertion cannot reliably keep a large or irregular Markdown file organized, use a hash table as the intake representation inside that same Markdown file. The file layout must remain `章节哈希表在前 -> 详细内容在后`; this is a fallback for storage, not a reason to create another file.

- Put a `## 章节哈希表` section at the front of the Markdown file, before the detailed content section. Each physical line is one canonical chapter key, for example `学科/章节编号/章节名称 -> {anchor: "#chapter-1", sources: ["图片001", "图片005"], status: "已保存"}`.
- When another image belongs to an existing chapter key, update that exact line's source list, content references, and status; never create a second hash-table line for the same chapter. The hash-table line is the single-row aggregation for that chapter.
- Put the full readable material after the table under the referenced chapter anchor, keeping the same chapter's detailed content together whenever safe. Preserve image order in the content and source references; do not replace the full material with only a summary.
- If no chapter key can be established confidently, append a new `待归类内容` key-value line in the front table and put its detailed content at the end of the post-table content area. Do not force it into an existing chapter line.
- Before generating the graph, read the front hash table together with the detailed content after it, then expand the records into knowledge-point nodes without duplicating the same chapter's full content in multiple source sections.

4. Finish the intake before deriving highlights.

   - Confirm that every inventoried image has a saved status and source entry in the one Markdown file. Separate unreadable or conflicting items for later review.
   - Only after the image batch has been captured and organized, read each node's complete `知识内容` and all mapped questions, then derive `从内容提取出来的重点` according to the rule below.
   - Use the completed Markdown as the source for the one subject-level knowledge-network HTML file.

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

   Read the complete `知识内容` and all available `相关的题目` for the node before writing `从内容提取出来的重点`. The card may display the four sections in the order below, but the `重点` is a later synthesis, not an early excerpt made before the questions are understood.

   1. `知识内容` - preserve the original source content, textbook content, or other supplied course content as the node's main material. Add source-grounded explanations, definitions, conditions, formulas, procedures, and boundaries when needed, but do not replace the source/course content with a summary-only rewrite.
   2. `从内容提取出来的重点` - after reading both the node's `知识内容` and its `相关的题目`, directly distill what is actually important: the concepts, conditions, operations, distinctions, recurring ways the questions test them, and demonstrated error boundaries. Do not produce these points by splitting one sentence into several lines, rewrapping the original wording, or mechanically converting prose into bullets. The result must be a genuine abstraction supported by the content and questions, not a content-only excerpt or unsupported claim. For example, source text `马克思主义不是一句口号，也不是孤立的某一门学科。它是由马克思、恩格斯创立并由后继者不断发展的科学理论体系，研究自然、社会和人类思维发展的普遍规律。` should be distilled directly as `马克思主义是由马克思、恩格斯创立并由后继者不断发展的科学理论体系，研究自然、社会和人类思维发展的普遍规律。` The extraction keeps the definition, creators/developers, and research scope instead of mechanically preserving the introductory negations or splitting the sentence. A second example: source text `资本主义生产方式的形成和发展推动生产力发展，使社会生产的社会化程度不断提高；同时，生产社会化同生产资料资本主义私人占有之间的基本矛盾日益暴露，周期性经济危机频繁发生。这些资本主义社会的现实矛盾，为马克思主义的产生提供了社会根源。` should be distilled directly as `生产社会化同生产资料资本主义私人占有之间的基本矛盾日益暴露，周期性经济危机频繁发生，这些资本主义社会的现实矛盾，为马克思主义的产生提供了社会根源。` This removes the background development clause and preserves the core contradiction, its manifestation, and the causal conclusion. If there are no mapped questions yet, state that question evidence is unavailable instead of pretending the points came from questions.
   3. `相关的题目` - each mapped question must contain all four fields:
      - `题目` - the preserved stem/options/figure reference;
      - `自己的解答思路` - a complete, generalizable route for solving, not just a formula or answer. When the question is multiple-choice or fill-in, it may also include a logically derived speed method, with its conditions and failure boundary;
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
   - Check browser-console errors and broken local asset paths. Verify Markdown structure and actual LaTeX rendering for mathematical content: notation must be readable in the rendered card, not merely present as delimiters or raw source.
   - Run `scripts/validate_markup.py` on the Markdown source and every retained learning report. Do not accept a validator that only counts backslashes or delimiters; it must reject bare commands such as `\\frac` outside a math span.
   - Report any source-limited or unresolved material explicitly; do not silently call an incomplete graph complete.
