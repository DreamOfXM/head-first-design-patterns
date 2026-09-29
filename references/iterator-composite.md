# Iterator & Composite（中文：迭代器与组合，第 9 章）

## 它吸收什么变化
**迭代器**：变化的是聚合的内部表示（列表／定长数组／字典）与遍历走法（正序／隔项／反向）；不变的是客户端"逐个取元素"那段。把遍历搬进独立对象，存储就此私有。
**组合**：变化的是节点的深度与类型；不变的是"对整棵树施加同一个操作"。把操作在 Component 上定义一次，叶子与组合各自实现。
两半合起来把"客户端必须知道结构"这件事搬走——它不再认数组、不再认子节点数。

## 触发信号
- 同一个客户端方法里为不同集合开了不同循环语法（size()/get(i) vs length vs values()），循环体却一模一样 → 遍历没被抽象，加一个迭代接口而不是第三个分支
- 有公开 getter 直接把内部 list/array 交出去、客户端在其上循环 → 存储泄漏，接口要换成遍历把手
- 每接一个新数据源就多一个循环／多一处 instanceof → 客户端与聚合个数在线性相乘
- 聚合类上长出 first()/isDone()/previous() 之类游标方法 → 存储和遍历两个变化原因挤在一个类
- 客户端必须提前 break、交替走两棵树、跨元素持状态 → 需要外部迭代，内部迭代不够
- 第一次出现"元素里能装另一个集合"（菜单套菜单、页面里加分区）→ 真正的部分-整体嵌套，Composite 的入口
- 同一操作必须在任意深度跑（print、getPrice、isVegetarian），而客户端在自己递归 → 一次递归操作的收益正在被丢掉
- 调用前要先 instanceof 判节点类型 → 透明性缺失，统一接口没建起来

## 别上的情形
- 语言原生就能遍历（for/in、for..of、Sequence）：不上——什么都不写，直接遍历聚合；上了自造 Iterator 接口——与所有现成消费者失去互操作。
- 客户端只是"对每个元素做一件事"：不上外部游标；上了 hasNext()/next() 样板——把节奏控制权白白交出去，读起来更差。
- 元素还是平铺兄弟：不上——一个可迭代集合 + 一个循环就够；上了 Component 树——叶子继承到无意义的 child 方法，还得补异常管道，也别为此逼数据主人提前重构。
- 节点只带数据、操作在外面（嵌套 JSON／DTO）：不上 Composite；上了——新增字段要在每个节点类各改一遍（非本书）。
- 叶子与组合必须各自保持严格类型、客户端不许看见统一接口：不上透明版；上了——安全与透明拿不到两样。

## 更省的替代
1. 数据／配置：把可变部分做成**数据**——聚合内部字典只投影出 values() 序列（顺序与投影即配置）；组合需求先做成"平铺列表 + parentId 字段"。够：走法只有一种、层级只有一层。不够：同一个源要同时供正序与隔项两种走法。
2. 闭包／函数参数：内部迭代——`items.forEach(printItem)`、`map`／`reduce`，或在外面写一个递归函数 `total(node)` 吃掉数据树。够：客户端不控节奏、行为长在函数上。不够：要在遍历中途停、要在节点上带行为。
3. 单个注入对象：交出**一个**游标对象而不是集合——`createIterator()` 返回平台已有的迭代器／一个 generator；组合侧只注入一份"树 + 一次递归操作"。够：存储与走法各自单点变化。不够：结构本身会递归嵌套且客户端要平铺访问所有叶子。
4. 才轮到这两个模式：手写 Iterator 类只在平台遍历不了的结构上成立（跳步、嵌套、懒算）；Composite 只在"行为必须长在节点上、客户端不许知道节点种类"时成立——降级就拿不到任意深度统一施加操作这一条。

## 最小骨架
**伪代码（角色与方向）**
```
Aggregate.createIterator() -> Iterator     # 工厂 hook：由知道自家表示的那个类决定实例化谁
Iterator.hasNext() / next()                # 持有游标；一次性
Client: 只认 Iterator，看不见 ArrayList／数组／字典
Component = Leaf ∪ Composite（同一接口，含 child 操作 → 透明，换掉一部分安全）
Composite.createIterator() 返回压栈子迭代器的扁平遍历；Leaf 返回空迭代器（不是 null）
操作(print/getPrice) 在 Component 上定义一次，组合向下委托、叶子就地作答
调用方向：Client -> Aggregate/Component -> Iterator -> 回到 Client
变化点：存储结构｜遍历走法｜节点层级｜施加的操作
```
**Java**
```java
interface MenuComponent {                                          // 透明：叶子与组合同一接口
    String name();
    java.util.List<MenuComponent> children();                       // 叶子也答这个方法，给空的，不给 null
}
class Item implements MenuComponent {
    private final String name;
    Item(String name) { this.name = name; }
    public String name() { return name; }
    public java.util.List<MenuComponent> children() { return java.util.Collections.emptyList(); }
}
class Group implements MenuComponent {
    private final String name; private final java.util.List<MenuComponent> kids = new java.util.ArrayList<>();
    Group(String name) { this.name = name; }
    public String name() { return name; }
    public java.util.List<MenuComponent> children() { return kids; }  // 组合向下委托，叶子就地作答
    Group add(MenuComponent c) { kids.add(c); return this; }
}
class Walk {
    static void print(MenuComponent n, String indent) {              // 一个递归操作吃下整棵树
        System.out.println(indent + n.name());
        for (MenuComponent c : n.children()) print(c, indent + "  ");
    }
    static java.util.Iterator<MenuComponent> flatten(MenuComponent root) {  // 遍历走法与结构解耦：压栈
        java.util.Deque<MenuComponent> stack = new java.util.ArrayDeque<>();
        java.util.List<MenuComponent> out = new java.util.ArrayList<>();
        stack.push(root);
        while (!stack.isEmpty()) {
            MenuComponent n = stack.pop(); out.add(n);
            for (MenuComponent c : n.children()) stack.push(c);
        }
        return out.iterator();
    }
}
```
**Swift**
```swift
protocol MenuNode { func print(into out: inout String) }   // Component：叶子与组合同一接口
struct Item: MenuNode { let name: String
    func print(into out: inout String) { out += name } }
struct Group: MenuNode { let name: String; let children: [any MenuNode]
    func print(into out: inout String) { out += name; for c in children { c.print(into: &out) } } }
extension Group: Sequence {                  // 用平台协议，不手写 Iterator 类
    struct Leaves: IteratorProtocol { var stack: [any MenuNode]   // 递归结构的外部游标要存每层位置
        mutating func next() -> (any MenuNode)? { /* pop，非叶子则把其子节点压回 */ } }
    func makeIterator() -> Leaves { Leaves(stack: [self]) }
}
```
**TypeScript**
```ts
type MenuNode = { name: string; price?: number; children?: MenuNode[] };
class Menu { private items = new Map<string, MenuNode>();
  [Symbol.iterator]() { return this.items.values(); } }        // 存储不外泄，走法交平台
function* walk(n: MenuNode): Generator<MenuNode> {             // generator 委托替掉手写栈
  yield n; for (const c of n.children ?? []) yield* walk(c);
}
const total = (n: MenuNode): number =>                          // 一个递归操作吃下整棵树
  (n.price ?? 0) + (n.children ?? []).reduce((s, c) => s + total(c), 0);
```
三语分工：Java 段是本书语言的骨架（原书只有 Java 的 Iterator／Iterable 形状）；Swift／TS 段是现代语言映射（非本书）。

## 上了之后要盯的代价
- 游标对象是一次性的：重扫就问聚合要新迭代器；别为了省一次分配去给共享迭代器加 rewind，也别把一个迭代器交给两个消费者。
- remove() 要么做对（元素移位、null 收尾、next() 之前调用要报错），要么显式抛不支持；静默 no-op 是最贵的那种。
- 并发／遍历中改集合：语义未定义，多迭代器跨线程不要指望一致。
- 遍历不等于顺序：迭代只保证逐个访问，除非底层集合文档承诺顺序，别对结果排序号、切片、按下标取。
- 外部迭代递归结构要为每层保住位置（栈）；深树注意栈深与共享可变游标——只在客户端确实要控节奏时才付这个钱。
- 透明接口的账：叶子上挂着 add/getChild，只为不做类型检查；安全接口反过来把 instanceof 撒进每个客户端。这是取舍，不是教条。
- 只适用于部分节点的操作要有**故意选的**兜底（抛／什么都不做／中性值）：中性值别悄悄改语义——菜单不是"非素食"，它压根没这个属性。
- 遍历里靠 try/catch 吞不支持操作来跳过分组节点＝逻辑用异常：它会把真 bug 一起吞掉；剩下两条路是 instanceof（毁透明）或真中性实现。
- 缓存整棵子树的汇总值就必须挂失效钩子，add/remove 是最少的改写点，漏一个就是脏数据（非本书）。
- 组合节点的身份若只是名字／描述，用实例而不是每个聚合一个子类。

## 形近模式判别
- 存储 vs 遍历：这个类被改的理由是"换了数据结构"还是"换了走法"？两个理由同时出现就是该拆成两个类。
- 外部 vs 内部迭代：谁控制节奏？客户端要 break／交替／持状态 → 外部迭代器；只是每个元素套一个函数 → 闭包。
- 手写迭代器 vs 平台迭代器：平台类型能不能直接遍历？能就交平台的，自造接口只为特殊走法。
- Composite vs 数据树＋外部递归函数：下一次改动是"加一个新操作"（Composite 帮你）还是"加一个节点类型/字段"（Composite 把改动乘以节点数，非本书）。
- createIterator() vs 客户端自己造迭代器：谁决定实例化——聚合知道自家表示，这槽位就是工厂 hook。

## 组合与框架替身
- Composite + Iterator 是本模式的正式配对：createIterator() 挂到 Component，组合返回把子迭代器压栈的扁平遍历，叶子返回空迭代器；**别返回只走一层的子节点迭代器**，也别返回 null。
- 现成替身（书证形状）：ArrayList 自带迭代器、字典用 values() 再取迭代器、需要反向／隔项时另有专门迭代器实现藏在同一个 hook 后面。
- 现代默认（非本书）：Swift 的 Sequence／Collection／IteratorProtocol（加 lazy 走大树、AsyncSequence 走流式子节点）；TS 的 Symbol.iterator ＋ generator（yield* 委托、AsyncIterator）；Python 的 __iter__ 返回 generator。直接实现平台协议，别手写 Iterator 类。
- 已经是现成树形状的东西（非本书）：SwiftUI 的视图树、React 元素树——任意深度统一渲染已经是这个模式，别再手写 Component 基类去套它。
- 常配：Null Object（叶子的空迭代器）；工厂 hook（决定造哪个迭代器）。

## 决策问句
1. 我是不是正在同一个函数里为第二个集合写第二种循环？是 → 抽象遍历；只此一处 → 本地遍历就好。
2. 有没有 getter 在往外送内部集合？把它换成"给我一个遍历"，存储就此私有。
3. 元素会不会装元素？不会 → 平铺列表 + 一个循环；会 → 再问操作是否要在任意深度统一施加。
4. 客户端要控节奏还是只要一个函数？前者外部迭代器，后者闭包／map。
5. 这个节点的行为该长在节点上，还是该长在外面那组递归函数上？答案决定 Composite 还是数据树。

## 证据
源文件：《Head First Design Patterns》1st ed.（Eric Freeman & Elisabeth Freeman, with Kathy Sierra & Bert Bates；O'Reilly, 2004）电子版，第 9 章，书页 pp.315-384（本文件引用的页区间 p.317-377）。换算：正文 PDF 页 = 书页 + 38。
迭代器引用点：p.317-327（暴露内部集合之害）、p.321-324（重复循环、封装遍历）、p.325-326（角色与游标）、p.332-335（平台迭代器优先、统一接口、工厂 hook）、p.336-338（定义、SRP、外部迭代、顺序不保证）、p.343-350（getItems 删除、一次性游标、remove、隔项迭代器）、p.351（每菜单一次调用的 OCP 问题）。
组合引用点：p.352-356（平铺优先、嵌套到来、定义）、p.358-363（角色、递归、一次调用打印全树）、p.367-371（透明换安全、部分节点才适用的操作、异常流）、p.377（缓存、子节点顺序与父指针、整树汇总）、p.368-370（CompositeIterator 压栈、NullIterator）。
标了（非本书）的条目：缓存需配失效钩子；Composite vs 数据树的"新操作／新节点类型"判据（该块 INFERRED: yes）；最小骨架与"现代默认""现成树形状"里的 Swift／TS／Python 映射（原书只有 Java）。
