# Factory（中文：工厂 —— 简单工厂 / 工厂方法 / 抽象工厂，第 4 章）

## 它吸收什么变化
- 变化轴：**这一轮要构造哪个具体类**。业务逻辑里每个 `new` 都是一条依赖边；类型集合一变，每条边都要重开（同一章的依赖计数：8 条 → 加一个地区 12 条）（非本书）。
- 不变的部分：构造之后那串稳定语句（prepare / bake / cut / box 式流程）。
- 搬走的是"选类"这一半，不是"创建"本身：**把创建圈起来，而不是假装它不存在** —— 抽象不能取消具体构造，只能把它关进一个可维护的入口（composition root）。要求"零具体引用"的架构等于没地方能造出任何东西。
- 三个子模式在同一条轴上解决不同问题，混谈会上错重量级：简单工厂 = 一个编辑点；工厂方法 = 子类决定 + 流程复用；抽象工厂 = 用组合替换整族配套部件。

## 触发信号
- 方法里有一段 if/switch 在按类型挑要 new 的对象，而其余语句多年不动 → 只把"选类"那段抽走（变/不变的切分是我对 p.112-113 的整理，非本书）。
- 同一段构造分支被复制进菜单 / 配送 / 后台等多个类，加产品要在 N 个文件同步改 → 简单工厂的首要判据：**一个编辑点**；工厂的价值随客户端数量增长（p.115；"复制的分支每份都要重开"这条失效方式，非本书）。
- 稳定 workflow 已存在，只有产品身份按部署 / 地区 / 租户变 → 工厂方法。
- 产品由多个**必须配套**的部件组装，跨家族混搭会产生非法组合 → 抽象工厂。
- 两个产品子类的唯一差别是"用了哪些组件对象" → 抽象工厂可把它们塌缩成一个类；若差别还包含行为（某地区覆盖 `cut()`，p.129），产品子类仍要留着。
- Review 里有人说"用 Factory 模式"，方案是一个类 + 一个静态 create 方法 → 按习惯用法命名它（simple factory / static factory），它没有子类钩子也没有可替换的多态实现（非本书）。
- 高一层（store / service）的文件里直接写得出具体产品类名 → DIP 判据（p.139-141）。

## 别上的情形
- 程序启动只构造一次的类：直接调构造器更清楚也更便宜；上工厂要付额外类 + 一层间接 + 产品增长时被迫改宽接口（这条"值不值"的汇总口径，非本书）。
- 只有一个调用方且只有一个产品：不上只是原地构造，没有任何级联；上了付的是仪式成本 —— 一个客户端没有杠杆可言（p.115 的杠杆前提是"多个客户端问同一个创建者"）。
- 要变的是**流程**而不只是产品：上工厂也管不住流程 —— 调用方 `create()` 之后可以跳过任何步骤（p.118-119 的质量控制讨论）；不上只是流程留在调用方，上了还多一层间接。那是模板方法/骨架的活。
- 只有原料不同却给每个地区复制整套 creator 层级：平行层级税，加一个地区 = 1 个 store + 4 个产品类（p.132 / p.165）。
- 把 DIP 读成字面禁令（不能持有具体类型变量、不能继承具体类、不能覆盖继承实现）：书里自己说每个真实程序都在违反它（p.143）。给稳定标准库类型（String 之类）套工厂、给每个 DTO 造接口都是负收益。
- 团队还读不懂 wiring：类图复杂度本身就是账（p.158 承认 "fairly complicated class diagram"）。

## 更省的替代
阶梯，从最便宜的开始，够用就别再升级：
1. **数据 / 配置**：把"变体"降级成一张表，变体是数据不是类。`enum Kind { case cheese, clam }` + 一个 `make(_:)` 表；TS `const MENU: Record<Kind, PizzaSpec>`。
2. **闭包 / 函数参数**：把钩子做成一个函数值传进共享流程，不需要继承。`func order(_ kind: Kind, _ create: (Kind) -> Pizza)`；TS `orderPizza(kind, create)`，`create = (k) => new CheesePizza(ing)`。
3. **单个注入对象**：构造器参数类型写成抽象（Protocol / 接口），具体对象在入口造好一次交进来。`init(ingredients: IngredientFactory)`；`def __init__(self, provider: PaymentProvider)`。
4. **才轮到工厂**：要"未知未来变体可插拔 **且** 流程被强制"→ 工厂方法；要"整族配套部件按部署整体替换"→ 抽象工厂。
不能降级的理由：当"造哪个类型"必须由**调用方之外的东西**（子类身份 / 注入的家族）决定，而流程代码必须写成不认识任何具体产品时，函数参数只是钩子的实现细节，抽象产品这一层必须存在，否则流程重新依赖具体类。
类型安全：公开一个裸 string 开关不算工厂设计 —— `createPizza("CalmPizza")` 能编译、运行时静默返回 null（p.135 / p.123；这条后果的表述，非本书）。键用 enum / sealed union / 类型常量，让拼错在编译期失败。

## 最小骨架
**伪代码（角色与方向）**
```
Client ──持有──▶ Creator（稳定流程 order()，不认识具体产品）
Creator ──钩子──▶ createProduct(kind) -> Product   ← 变化点：子类 / 注入的家族决定
Product ◀──实现── Concrete{Cheese,Clam}            ← 只在 composition root 出现
AbstractFactory ◀─组合─ Product（ prepare() 时向它逐个要部件 ）
```
**Java**
```java
enum Kind { CHEESE, CLAM }                                    // 键是 enum，不是裸 String
interface Dough { void prepare(); }                            // 抽象部件
abstract class Pizza { abstract void prepare(); }              // 抽象产品
class CheesePizza extends Pizza {
    private final Dough dough;                                 // 组合进来的抽象工厂产物
    CheesePizza(Dough dough) { this.dough = dough; }
    void prepare() { dough.prepare(); }                         // prepare 时向它要部件
}
class NYPizzaDough implements Dough { public void prepare() { System.out.println("thin crust"); } }
abstract class PizzaStore {
    final void order(Kind kind) {                               // final：稳定流程不许子类改顺序
        createProduct(kind).prepare();
    }
    abstract Pizza createProduct(Kind kind);                     // 变化点：子类决定造哪个
}
class NYPizzaStore extends PizzaStore {
    Pizza createProduct(Kind kind) {
        if (kind == Kind.CHEESE) return new CheesePizza(new NYPizzaDough());   // 唯一 new 的地方
        throw new IllegalArgumentException("no such product: " + kind);        // 不认识的键要响
    }
}
```
**Swift**
```swift
// ↓↓↓ 配套，不是模式内容
struct Dough { let name: String }                          // 部件
struct CheesePizza: Pizza { let ing: IngredientFactory
    func prepare() { print(ing.dough().name) } }

protocol Pizza { func prepare() }                          // 抽象产品
enum Kind { case cheese, clam }                             // 键是 enum，不是 String
protocol IngredientFactory { func dough() -> Dough }        // 抽象工厂：一族部件
protocol PizzaStore { func make(_ kind: Kind, _ ing: IngredientFactory) -> Pizza }
extension PizzaStore {                                     // 稳定流程留在骨架里
    func order(_ kind: Kind, _ ing: IngredientFactory) { make(kind, ing).prepare() }
}
struct NYStore: PizzaStore {                               // 变化点 = 选了哪个 conformer
    func make(_ kind: Kind, _ ing: IngredientFactory) -> Pizza { CheesePizza(ing: ing) }
}
enum Root { static func build() -> PizzaStore { NYStore() } }   // 唯一 new 的地方
```
**TypeScript**
```ts
// ↓↓↓ 配套，不是模式内容
type Dough = { name: string }
const nyIngredients: IngFactory = { dough: () => ({ name: 'NY dough' }) }
const use = (i: IngFactory) => { i.dough() }

type Pizza = { prepare(): void }                     // 抽象产品
type Kind = 'cheese' | 'clam'                        // union，不用裸 string
type IngFactory = { dough(): Dough }                 // 抽象工厂（一族部件）
const order = (k: Kind, create: (k: Kind, i: IngFactory) => Pizza, i: IngFactory) =>
  create(k, i).prepare()                             // 流程：只认抽象
const nyCreate: (k: Kind, i: IngFactory) => Pizza =
  (k, i) => ({ prepare: () => use(i) })              // 变化点：换这个函数
export const store = { order: (k: Kind) => order(k, nyCreate, nyIngredients) }  // root
```

## 上了之后要盯的代价
- 类数量：抽象工厂"一堆新类，每个原料一个"（p.146）；换来的是"改一处"，不是"改得少"。
- 宽接口耦合：抽象工厂加一个产品角色 = 接口要改 + 每个具体工厂都要改（p.158-159）。
- 平行层级（工厂方法税）：creator 与 product 必须成对增加，两边一起改才配得上（p.132）。
- 静态工厂变体把创建**冻结**：静态方法无法被子类改掉创建行为，将来要按地区/租户变就得退回"实例 + 接口"（p.115）。
- 间接层找错：产品没被造出来 / 造错了，调试路径变成 client → 钩子或注入的家族 → 入口，栈里看不到"是谁决定用这个类的"。
- "子类决定" ≠ 运行时自适应：具体身份由**你 handed 了哪个子类**决定，基类流程对产品是盲的（p.122 / p.134）。想要运行时换 = 组合一个可替换的工厂对象，不是工厂方法。
- 创建不会消失：抽象工厂对象本身仍要在某处被构造 —— 选择权只是移到 creator / 入口（p.152）。
- 工厂方法只有一个具体 creator 时也成立：creator 只依赖抽象产品，产品重写不会打破它（p.135）；别因为"还没有第二个子类"就退回 `new`。

## 形近模式判别
- 简单工厂 vs 工厂方法：方法体长得一样，但后者坐在继承契约里 —— 流程被复用、产品集开放扩展；前者是"一次性"，后者是"框架"（p.135）。
- 工厂方法 vs 抽象工厂：决定性问题 —— **变的是一个产品还是一族配套部件？** 一个产品 + 固定流程 → 继承（工厂方法）；多部件按部署替换 → 组合（抽象工厂）（p.158-159）。
- 工厂 vs 策略：策略换"同一件事怎么做"，工厂换"造出哪个东西"；抽象工厂的每个 create 方法本身就像个工厂方法（p.158）。
- DIP ≠ "面向接口编程"：后者只要求高层用接口；DIP 要求**高低两层都指向抽象**、低层的具体细节不得向上泄漏，判据是依赖箭头的方向（p.139-141）。工厂只是实现 DIP 的手段之一，组合、配置、容器同样能反转。
- 两者可合用：creator 的工厂方法决定产品身份，产品内部注入原料家族；别把家族的选择埋在产品深处，否则它不再是每 store 一次的决定（p.160-161）。

## 组合与框架替身
- 与模板方法：基类流程 + 抽象钩子就是工厂方法的结构；把流程标 final 只是可选强制。
- 与组合/注入：抽象工厂几乎总是"注入一个部件家族"，与继承无关。
- 现代替身（非本书）：Swift 用协议初始化器（`init(duck: Duck)`）+ 一个 `AppCompositionRoot` 持有全部具体构造；TS/Node 用单个 `container.ts` / `main.tsx` 或 DI 容器（InversifyJS、Nest provider）；React 用 Context / props 把"已造好的对象"传下去，组件不 import 具体实现模块；Python 用 `main.py` / `deps.py` + FastAPI `Depends`；Spring `@Configuration` 已是"入口造具体、下游只认抽象"的形状 —— 有容器就直接用，别再手写 ServiceLocator。

## 决策问句
1. 这段代码里"选具体类"的语句和"跑流程"的语句能不能分成两段？只抽前一段，别把整个方法抽走。
2. 有几个调用方会构造同一族产品？不到两个就别上；三个以上才谈工厂的价值。
3. 变化的是**一个产品**还是**一族配套部件**？前者工厂方法，后者抽象工厂。
4. 变体之间的差别只有"用哪些部件"，还是也有行为差别？只有部件差别才塌缩成一个产品类。
5. 最终的创建落在哪个文件？答不出来 = 没有 composition root，工厂只是把 `new` 藏起来了。

## 证据
- 源文件：《Head First Design Patterns》1st ed.（Eric Freeman & Elisabeth Freeman, with Kathy Sierra & Bert Bates；O'Reilly, 2004）电子版，第 4 章，书页 pp.109-168。换算：正文 PDF 页 = 书页 + 38。
- 书页区间：thinking about `new` p.110-113；简单工厂与注入 p.114-117；加盟与流程控制 p.118-121；抽象 PizzaStore / 声明钩子 p.120、p.125、p.129；子类如何决定 p.122；平行层级 p.132；定义与比较 p.134-135；Master/Student 与依赖统计 p.136-138；DIP p.139-143；抽象工厂 p.146、p.150-152、p.156、p.158-162；谜题答案 p.165。
- 标了（非本书）的条目：变/不变切分与"分支被复制"反模式、simple factory 属习惯用法定性、裸 string 键的运行时后果、依赖计数（8→12）与"数构造点不数字段/导入"、"to factory or not to factory" 的成本汇总口径、以及全部现代框架替身（协议初始化器、composition root、DI 容器、Context/props、FastAPI/Spring）。
- 其余条目（含 DIP 与三条指导的 aspirational 说法）均可指回上述页码。
