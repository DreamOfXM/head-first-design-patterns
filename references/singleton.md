# Singleton（中文：单例，第 5 章）

> 这是一份**警告型**参考。第 5 章自己就把它写成"最简单但最难写对"的模式，全章大半篇幅在拆自己的实现（线程、classloader、子类化、GC）。默认答案是不用它。

## 它吸收什么变化
- 变化轴：**谁能决定这个类存在几个实例**。把答案收进类自己（私有构造 + 静态访问点），外部就再也造不出第二个。
- 不变的部分：这个类本来要干的领域工作 —— 单例不吸收任何业务变化，它只吸收"实例数量与访问入口"这一件事。
- 搬走的是"由调用方负责共用同一个对象"，代价是每个使用点都不再声明这个依赖。

## 触发信号
- 两个活对象同时存在会**产生错误结果**，而不只是浪费资源：连接池/线程池各开一份 → 上限翻倍；缓存各存一份 → 同一个 key 读到不同答案；preference/registry 两份 → 一边写了另一边看不见 → 唯一判据是**会不会算错**，不是省不省代码（p.170 / p.174 的用例清单；判据口径，非本书）。
- 天然单数的资源：设备驱动、对话框、logger、共享注册表 → 本章列的正当用例；仍需先回答上一条。
- 有一个昂贵且共享的对象需要延迟构造 → lazy instantiation（p.173）；但要接受下面第 1 级线程账。
- 反过来：**"到处都能拿到很方便" 不是触发信号** → 那是把全局变量打扮成模式，属于别上的情形（非本书）。

## 别上的情形
- 只是多处要同一个对象：那是 wiring 问题。不上会怎样：多写一个构造参数；上了付什么账：真实输入从签名里消失，测试要动全局才能替换或复位（非本书）。
- 需要按地区 / 租户 / 测试替身给出不同实例：不上只是多接线；上了的单一实例本身成了障碍，只能靠放宽构造器（毁掉唯一性）绕开。
- 实例数量需要可变（对象池）或需要被释放：不上只是构造点分散；上了付什么账 —— 静态字段是一条永久 GC root，实例和它够到的一切活到 loader 结束（这条生命周期推论，非本书）。
- 想靠继承派生变体：私有构造挡住了扩展；把可见性放宽到 protected/public 立刻毁掉唯一性；而且朴素子类还共用基类那个静态字段。真要做必须在基类建实例注册表（instance registry），本章先让你回答"你到底得到什么"（p.185）。"用显式常量标志 + protected 构造把这个决定写可见"是泛化写法（非本书）。
- 运行时不受你控的环境（库、容器、插件、hot deploy）：多个 classloader 各有命名空间，同一个 Singleton 类被两个 loader 加载就是两个活实例 —— "每应用一个"在这种环境是假话（p.184）。不上只是每处传对象；上了付的是"你以为只有一份"的调试时间。
- 代码库里已经好几个 `X.getInstance()`：本章明说单例要**省着用**，需要很多单例的代码库要先审视设计，而不是再加一个（p.185）。不上只是补 wiring；上了付的是 ownership 与依赖图彻底 undocumented。别把它当服务定位策略。

## 更省的替代
阶梯，从最便宜的开始：
1. **构造参数**：`init(cache: Cache)` / `def __init__(self, cache: Cache)`，在 `main()` / App 入口造一次传下去 —— 多数场景到这里就够了，这不是模式，这是接线（非本书）。
2. **模块作用域实例**：ES module `export const cache = new Cache()`（单个 bundle 内每进程只求值一次）；Python `_cache = Cache()` 在 import 时（CPython 的 import lock 覆盖首次 import）。
3. **语言自带的 once**：Swift `static let shared = Cache()` —— 惰性且原子，不需要你写 DCL；共享状态被并发修改时用 `actor`。
4. **才轮到 Singleton**：唯一性必须**在任何入口下**由类自己守住（否则外部能再 `new`、能重新赋值全局引用）。全局变量给的是访问，不给唯一（p.185）—— 这是唯一不能靠降级解决的理由。
不能降级但也不该上：全静态类是"伪单例"，自包含时够用，多个类互相引用时栽在静态初始化顺序（p.184）。

## 最小骨架
**伪代码（角色与方向）**
```
class Sole:  private init()            ← 外部无法构造
  static field uniqueInstance          ← 永久 root，谁都能读
  static getInstance() -> Sole         ← 唯一访问点（也是全局点）
  doWork()                             ← 领域职责，与"实例管控"混在同一个类
```
**Java**
```java
final class Cache {                                            // final：拒绝子类化陷阱
    private static final Cache SHARED = new Cache();             // 急切初始化：类加载保证原子
    private final java.util.Map<String, String> store = new java.util.HashMap<>();
    private Cache() {}                                           // 唯一性由这里守
    static Cache getInstance() { return SHARED; }                 // 唯一访问点＝全局点
    String get(String k) { return store.get(k); }                 // 领域职责与实例管控混在同一个类
}
class Service {
    final Cache cache;                                            // 默认写法仍是注入：依赖留在签名里
    Service(Cache cache) { this.cache = cache; }
}
```
**Swift**
```swift
final class Cache {                           // final：拒绝子类化陷阱
    static let shared = Cache()               // 急切/惰性都由语言保证原子
    private var store: [String: String] = [:]
    private init() {}                         // 唯一性由这里守
    func value(_ k: String) -> String? { store[k] }
}
// 但默认写法是注入：
struct Service { let cache: Cache }           // 依赖留在签名里
enum Root { static let service = Service(cache: .shared) }
```
**TypeScript**
```ts
class Cache { private static inst?: Cache
  private constructor() {}
  static getInstance(): Cache { return (Cache.inst ??= new Cache()) } }  // 单线程 isolate：不需要锁
export const cache = Cache.getInstance()   // 更省：module 顶层拿一次，每进程一次
export function makeService(c: Cache = cache) { return { run: () => c } }  // 测试可传替身
```

## 上了之后要盯的代价
线程安全阶梯（本章的主线，按顺序读）：
1. **经典惰性版** `if (uniqueInstance == null) uniqueInstance = new Singleton()`：两个线程可以同时通过 null 检查、各造一个并返回不同对象。危险窗口是**第一次调用**，不是后面 —— 别用"字段只被赋值一次"说服自己（p.178-179 / p.188）。
2. **`synchronized getInstance()`**：正确，但每次调用都排队，而互斥只有第一次需要。本章给的数字：方法同步可让性能降到约 1/100 —— 这是 2004 年前后 JVM 的测量口径，现代运行时必须自己重测（非本书）。
3. **DCL（双重检查锁定）**：锁外查、加类锁、锁内复查，只在第一次付同步。字段**必须 `volatile`**，否则其他线程可能观察到未发布/半构造的引用。且它**与版本相关**：Java 1.4 及更早的 JVM 上 `volatile` 实现会让 DCL 静默失效（p.182、p.186）。运行时不由你控的库环境别写 DCL。Swift `static let`、Node 单线程 isolate 根本不需要它（非本书）。
4. **急切 / static initialiser**：声明处直接赋值，`getInstance()` 只 return —— 语言保证任何线程读到静态字段前对象已造好。代价：从类加载到关闭一直占内存，没人用也在。
5. 选择口径：**按实测代价选**，访问点是冷的就别同步；对象总要用的就急切；只有热路径且必须惰性才 DCL。本章自己嫌 DCL 对没有性能诉求的场景是 overkill（p.183 / p.189；"按实测选"这条，非本书）。
其他账：
- 类同时管两件事（管控自己的实例 + 干业务的活），违反一类一责；本章为简单起见接受这笔账，若管控逻辑要复用就抽出去而不是复制粘贴（p.185）。
- 静态访问点**隐藏依赖**：真实输入不出现在签名里，测试无法替换或复位，用例之间互相泄漏状态、某个测试只有跑在另一个之后才通过。本章未讨论测试性，这条由"全局访问点"直接推出（非本书）。
- GC 只被自己引用的实例：Java 1.2 之前会被回收，下次访问拿到全新对象、共享状态静默复位；现代 JVM 别再为此写 keep-alive 注册表（p.184、p.186）。

## 形近模式判别
- vs 全局变量：决定性问题 —— **谁能决定存在几个**。全局引用人人可改；单例由类守住数量。
- vs 全静态工具类：决定性问题 —— **有没有需要共享的可变状态**。没有就用静态函数；有就回到对象世界。
- vs 容器/工厂提供的"每作用域一个"：决定性问题 —— **唯一性由谁保证**。容器由配置界定作用域、可替换可测；单例把它硬编码进类。
- vs Facade（都提供一个统一入口）：Facade 收的是"很多部件的调用顺序"，Singleton 收的是"实例数量"；`HomeTheaterFacade` 不需要 `shared`。

## 组合与框架替身
- 常与工厂（工厂造的唯一对象）、连接池/缓存/logger/device driver 一起出现 —— 这些就是本章的正当用例清单（p.170 / p.174）。
- 现代替身（非本书）：Swift `static let`（原子惰性 once）、并发可变态用 `actor`；TS/Node 的 ES module 顶层实例（每 registry 一次求值）；Python module-level 实例或 `functools.lru_cache` 包一个 `get_foo()`；DI 容器的 singleton scope（InversifyJS / Nest provider / Spring 单例 bean / FastAPI `Depends`）。容器版本比手写 `getInstance()` 好换好测，需要"进程内唯一"时优先用它。

## 决策问句
1. 同时存在两个实例会**算错**吗？说不出具体的错误，就是想要全局访问点而不是单例。
2. 测试或另一个租户需要假实例吗？需要 → 构造参数注入，别用静态访问点。
3. 访问点是否落在多线程热路径？不在就别加同步；在就先测再一次定策略。
4. 这个类将来要不要被继承、被替换、被释放？任一为"要"，单例的结构就在跟你对着干。
5. 代码库里已经有几个 `X.shared`？超过两三个 → 先补 wiring 与入口，再加单例是在掩盖它。

## 证据
- 源文件：《Head First Design Patterns》1st ed.（Eric Freeman & Elisabeth Freeman, with Kathy Sierra & Bert Bates；O'Reilly, 2004）电子版，第 5 章，书页 pp.169-190。换算：正文 PDF 页 = 书页 + 38。
- 书页区间：开场 Q&A 与全局变量对比 p.170；经典实现与剖析 p.173；Confessions 访谈 p.174；定义 p.177；多线程问题 p.178-179；四个选项 p.181-182（同步 / 急切静态初始化 / DCL + volatile / Java 1.4 失效警告）；回到巧克力工厂与答案 p.183、p.189；Q&A（classloader、GC、全静态类、子类化、SRP、省着用）p.184-185；要点清单 p.186；BE the JVM 答案 p.188。
- 标了（非本书）的条目："唯一判据是两实例会不会错"的整理口径、"方便不是理由"、首选注入而非管控（构造参数 / 模块作用域实例）、实例注册表之上的显式标志+protected 构造写法、实例永不释放的生命周期推论、隐藏依赖导致测试互相泄漏、"1/100 需重测"、"按实测代价选线程策略"、Swift `static let`/`actor` 与 ES module / `lru_cache` / DI 容器替身。
- 本章未提供多语言实现，所有非 Java 写法均属现代补充（已逐条标注）。
