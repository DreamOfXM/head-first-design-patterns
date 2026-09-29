# 形近模式判别（每对一句决定性问题）

按形状分模式一定会判错——同接口 + 转发的类，可能是代理、可能是装饰者、也可能是适配器。
**只有意图能分开它们。**下面每对给一个能当场回答的问题，答案要在你的变化句里。

| 对手 | 决定性问题 | 答案 → 结论 |
|---|---|---|
| Strategy vs State | 换掉它的是谁？ | 外部配置/构造期决定 → Strategy；对象自己收到事件后换 → State（第 10 章） |
| Strategy vs Template Method | 变的是整个算法，还是固定骨架里的某几步？ | 整体可换 → Strategy；骨架不变、步骤可变 → TM（第 8 章） |
| Strategy vs Decorator | 是替换一个做法，还是叠加一层职责？ | 替换 → Strategy；叠加且类型不变、可叠多层 → Decorator（第 3 章） |
| Decorator vs Adapter | 被包对象的对外类型变了吗？ | 没变、加了行为 → Decorator；行为没变、接口变了 → Adapter（第 7 章） |
| Adapter vs Facade | 你要匹配一个既有契约，还是设计一个更简单的新入口？ | 契约已存在且必须服从 → Adapter；入口由你定 → Facade（第 7 章） |
| Proxy vs Decorator | 被包对象在包装时是否已经存在？ | 已存在、只是加计算 → Decorator；代理可以决定**根本不造**或延迟造 → Proxy（第 11 章） |
| Proxy vs Facade | 调用方拿到的是同一个接口还是更小的接口？ | 同接口且守门 → Proxy；更宽的简化入口且不隐藏部件 → Facade |
| 简单工厂 vs 工厂方法 vs 抽象工厂 vs Builder | 谁决定造什么、决定几次？ | 一个 switch 集中造（非 GoF）；子类决定**一个**产品 → 工厂方法；一次决定**一族**协同部件 → 抽象工厂；分步装配复杂对象 → Builder（第 4 章、附录） |
| Observer vs Mediator vs Chain of Responsibility | 通信形状是什么？ | 一事件多收件人 → Observer；多伙伴互相调用、规则散落 → Mediator；一请求多候选按序尝试 → CoR（第 2 章、附录） |
| Iterator vs Composite 自带递归 | 调用方要不要控制流（早停、交错、跨层过滤）？ | 要 → 迭代器；只是"对整棵树做一次操作" → 递归方法（第 9 章） |
| Composite vs 树状数据 + 外部函数 | 以后主要加**操作**，还是加**节点类型/字段**？ | 加操作 → Composite 帮你；加节点类型 → Composite 让你每处都改（第 9 章） |
| Singleton vs 全局变量 vs 注入 | 存在两个实例会**出错**吗？ | 会（连接、设备句柄、计数器语义）→ Singleton；只是"方便到处拿"→ 那是全局变量穿了模式的衣服（第 5 章） |
| Command vs 闭包 | 这个动作要不要被存起来、排队、序列化、撤销？ | 都不要 → 闭包；要日志/撤销/队列 → 命令对象（第 6 章） |
| Template Method vs 框架生命周期钩子 | 你在写的骨架，框架是不是已经给了？ | 框架已给（React 生命周期、UIKit、SwiftUI `.task`）→ 用它的钩子，别再造抽象类（第 8 章） |
| Flyweight vs Prototype vs Memento | 压力在实例**数量**、实例**创建**，还是实例**历史**？ | 数量 → Flyweight；创建 → Prototype；历史 → Memento。注意 Flyweight 与 Prototype 方向相反，同一类型上别同时做（附录） |
| Bridge vs Adapter vs Decorator | 变化压力在哪条轴？ | 抽象与实现两轴同时演进 → Bridge；接口不对 → Adapter；职责像洋葱一样长 → Decorator（附录） |
| State vs 合并成一个 flag | 那个 flag 有没有自己独立的变化理由？ | 有 → 它是独立状态，别合并；只是同一状态的两个读数 → 合并更省（第 10 章） |
| Visitor vs 枚举 + 单函数 switch | 节点类型稳定且新操作不断到达吗？ | 是 → Visitor 的思想值得借；否则一个针对枚举的函数更便宜，别为纯正性上双层分派（附录） |
| 抽象类 vs 接口 | 有要共享的**状态**吗？ | 有状态要共享 → 抽象基类；只需类型契约 → 接口/协议（第 1 章"要不要把 Duck 也做成接口"：不） |
| MVC 里的 Controller vs ViewModel | 逐个角色问：谁是 Subject？谁能被换掉？谁在递归渲染？ | 答不清就别声称在用 MVC（第 12 章） |

## 三条通用判别纪律

1. **按名字分派是坏味道，按意图命名才是设计。**类型测试（`instanceof` / `as?` / `typeof`）出现在业务逻辑里，通常说明有一条变化轴没被隔离；但反过来，为了让图"纯正"而消灭合理的类型分派（值类型、枚举、代数数据）也是错的。
2. **同一个类型可以同时扮演两个角色。**第 9 章里 Component 既是节点又是叶子入口——不要为此专门加一个"根/非根"标志位。
3. **类别对上 ≠ 模式对。**Decorator 归结构型却在做行为型的事（第 13 章）。类别只用来缩小搜索范围，最终裁决看变化句和代价。
