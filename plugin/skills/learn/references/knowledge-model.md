# 通用知识模型

learn 只定义跨学科平台实体和输出边界。领域 skill 负责实体内部的认知结构。

## Subject

一个 Subject 拥有一个 canonical Markdown、一个知识网络 HTML、一个 learner_state 和一个持久化任务状态。原始图片、试卷、解析文件和外部来源不被覆盖、改名或删除。

## Module

Module 表示学科、课程、章节、单元或目录。它只负责导航和稳定层级，不自动成为知识卡或题目。

## Knowledge node

Knowledge node 由领域模型定义正文结构。通用 learn 不规定所有学科使用同一个 Card Schema，也不把数学、政治、408 或其他学科的卡片字段硬编码在入口。

每个 node 仍需要稳定 ID、标题、来源引用、关联关系引用和可检索入口。领域模型可以提供 definition、theorem、formula 等专属类型，也可以使用通用的主知识点/关联知识点投影。

## Relation

Relation 是有向的、可追溯的连接。平台要求稳定的 from、to、type 和 reason 字段；关系类型和数学语义由领域模型提供。

## Progress

Progress 分开保存学习完成状态、主动缺口、知识掌握和题目掌握。学习状态不能只由文件存在或页面打开推导。

## Output contract

生成或更新时只写回当前 Subject 的 canonical Markdown、知识网络 HTML、learner_state 和 task-state。领域中间记录不能成为第二份并行知识库。
