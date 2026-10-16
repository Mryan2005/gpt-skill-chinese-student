# 数学 Semantic Relation

## 层级与语义关系分开

层级关系用于章节导航：`module.parentId`、`card.parentId`、`part_of`。语义关系用于方法选择、条件依赖和横向理解：`prerequisite`、`alternative`、`used_by` 等。两者不能都塞进无类型 `relations[]`。

## Relation schema

```json
{
  "id": "ratio-alternative-root",
  "from": "ratio-test",
  "to": "root-test",
  "type": "alternative",
  "why": "两者都可处理部分正项级数，但比值极限为 1 时比值判别法失效，根值法可能仍有信息。",
  "sourceIds": ["series-method-map"],
  "status": "VERIFIED"
}
```

`from` 和 `to` 都是已存在的 Card/Module ID；`from != to`；`type` 非空；`why` 必须解释该方向的数学含义，不能写“二者有关系”或“应放在同一知识链”。

## 允许的语义类型

```text
prerequisite   前置
derives        推出
implies        蕴含
equivalent     等价
special_case   特例
generalization 推广
part_of        属于
method_for     方法
used_by        应用于
alternative    替代
contrast       对比
often_confused 易混
```

所有记录都保存为有向边，即使数学语义具有对称性；如需双向导航，显式保存两条方向相反且 why 各自成立的边，不使用无方向的 `A ↔ B` 字符串。

## 方向示例

```text
可导 --implies--> 连续
极限定义 --prerequisite--> 导数定义
比值判别法 --alternative--> 根值判别法
比值判别法 --used_by--> 幂级数收敛半径
```

不要把“连续 ↔ 可导”当作等价，也不要把导数定义和极限定义写成同层同义关系。

## Bridge Gate

Bridge 的 `outgoingRelationIds` 至少包含一条真实关系，且每条关系的 `from` 必须是该 Bridge，或由 `branch.targetCardId` 指向一个真实目标。没有出边、只画 ASCII 选择图、或只有文字建议而无 typed relation 时报告 `EMPTY_BRIDGE`。
