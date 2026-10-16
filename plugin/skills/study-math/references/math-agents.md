# 数学专项代理分工

## 共享合同

每个代理收到相同的 subject、原始来源、结构化记录路径、canonical 输出路径和 batch ID。代理只写自己的报告，例如：

```text
<project>/.codex/math-reports/<batch-id>/source-extraction.md
<project>/.codex/math-reports/<batch-id>/question-structure.md
<project>/.codex/math-reports/<batch-id>/solution-answer.md
<project>/.codex/math-reports/<batch-id>/card-relation-map.md
```

代理不能直接写 canonical Markdown、知识网络 HTML、`learner_state.md`、`.codex/task-state.md` 或 `design_memory.md`。主 `study-math` skill 是唯一合并者。

每份报告使用普通 Markdown 和带定界符的 LaTeX；运行 `scripts/validate_markup.py`；标记证据状态和不可读边界；不把外部理解或推导写成原始材料/官方答案。

## 四个角色

### 1. 数学源材料提取

返回文字、公式、题号、选项、分问、图形、版面关系、跨页连续性和 unreadable regions。只提取，不擅自解题、补题或修复公式。

### 2. 数学实体分类与题目结构化

把来源分类为 metadata、knowledge content、question、solution、answer 等；生成稳定 Question ID；拆分题组；保存题干片段、选项、分问、图形、MathObject 和题目完整性状态。

### 3. 数学解析与答案验证

检查解析步骤是否完整，识别空缺/截断，区分 official/historical/derived answer，并根据完整题干和证据做独立计算或证明检查。没有证据不能填写官方答案。

### 4. 数学知识卡与关系映射

为每个知识任务选择 Card Type，拆分非原子卡，选择唯一 primary card 和 secondary tags，建立层级与 typed semantic relations，说明每条边的 why。Bridge 必须落到真实 outgoing relation。

## 合并顺序

```text
提取报告
→ 来源分类/题目拆分
→ 解析与答案证据
→ Card/Relation 映射
→ validate_math.py
→ 读取完整题目后生成卡片重点
→ canonical Markdown/HTML
→ validate_markup.py 与实际渲染
→ Math Exam Readiness Gate
```

报告冲突时保留冲突和 `待核实` 边界，不用多数票选择方便的答案。
