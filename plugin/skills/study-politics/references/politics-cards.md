# Politics Card Schema

## Common derived shape

~~~json
{
  "id": "politics-card-001",
  "type": "concept",
  "title": "实践是认识的来源",
  "coreStatement": "认识来源于实践。",
  "recallPrompt": "认识的来源是什么？",
  "sourceRefs": [
    {
      "sourceId": "src-book-p42-p3",
      "locator": "paragraph-3"
    }
  ],
  "derivedVersion": 2,
  "status": "ACTIVE"
}
~~~

Source quote remains in the Source record. coreStatement, recallPrompt, comparison, confusion, and question mapping are Derived content.

## Types

- concept：定义对象、范围、关键词和最小例子；
- principle：保存命题、条件、因果方向和适用边界；
- canonical-expression：保存必须准确回忆的教材原话及其来源；
- comparison：并列相近概念、区分维度和反例；
- confusion：记录选择题中易互换的词和判断边界；
- timeline：保存事件顺序、阶段、转折和来源；
- policy-framework：保存政策目标、对象、措施和条件；
- problem-pattern：保存题干信号、第一判断和选项排除路径。

## Canonical wording

Canonical-expression 卡必须同时展示：

~~~text
Source quote
Source locator
Derived recall prompt
Derived distinction or application
~~~

不能把 AI 改写的句子标记为教材原话。
