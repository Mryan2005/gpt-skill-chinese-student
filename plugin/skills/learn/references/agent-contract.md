# 通用代理合同

复杂学习批次可以使用隔离报告。代理报告不是 canonical Markdown、知识网络 HTML、learner_state、task-state 或 design_memory。

## Shared contract

- 每个代理收到相同的 subject、来源路径、当前输出路径和 batch ID。
- 每份报告保存到 project/.codex/learning-reports/<batch-id>/<role>.md。
- 报告标记原始材料、外部补充、题目推导、官方解析可读部分和待核实。
- 代理不覆盖原始文件，不把外部内容写成官方答案，不隐藏不可读边界。
- 代理运行当前 skill 的 Markdown/LaTeX validator。
- 主 learn skill 读取全部报告，处理冲突，并按当前领域模型合并。

## Roles

### Source extraction

提取来源文字、公式、图片、表格、页码、版面关系和不可读边界。不要擅自解题或补写。

### Content refinement

把已提取材料整理为可理解的来源内容、条件、边界和待核实点。不要决定领域专属卡片类型或最终关系。

### Question and example mapping

识别独立题目、题型、原题号、题干、选项、分问、图形、解析和答案证据。不要修改知识卡。

### Domain mapping

根据当前领域模型选择卡片结构、题目映射和语义关系。数学批次读取 study-math 的 math-agents.md；其他领域可以提供自己的代理合同。

## Merge rule

领域代理只提供报告。主 skill 保持一个 canonical writer，并在写回前运行通用与领域 Gate。
