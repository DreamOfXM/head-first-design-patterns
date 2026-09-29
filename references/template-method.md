# Template Method（中文：模板方法，第 8 章）

## 它吸收什么变化
变化轴只有一个：同一条有序流程里，某 1-2 个步骤的**做法**不同；步骤的**顺序与集合**不变。
固定骨架留在高层（父类／协议扩展／自由函数），可变步骤声明成待填槽位下沉给子类。
它搬走的不是重复行数，而是"流程知识散在每个变体里"——调一次顺序要改 N 处。

## 触发信号
- 两个以上类跑同一段多步流程，diff 显示调用顺序一致、只是 helper 换了名字 → 骨架可以固定，本模式才成立
- 每个子类都重写同一个编排方法，重写体几乎同形、只换 helper → 先把流程收到上层，再把步骤泛化成 brew / addCondiments 这类通用名
- 调用方开始把流程原地抄一遍 → 骨架正在外泄，收到唯一属主
- 新变体只需实现一两个方法就能跑通 → 粒度合适（判据：抽象步骤少而粗）
- 需求要求"同一变体里步骤顺序不一样"或"少一步/多一步" → 这不是触发信号，是反指信号
- 有人问"这个类能不能不继承也能复用流程" → 先看替代阶梯，别先看继承

## 别上的情形
- 只有"造哪个具体类型"在变：不上会怎样——多一个 if 分支；上了付什么账——一整套抽象方法只为返回一个对象。该用 Factory Method（本章明确它是模板方法的特化）。
- 整个算法在换而不是某一步在换：不上会怎样——多几个并列函数；上了付什么账——把整块算法拆成槽位，骨架被迫为每个算法存在。该用 Strategy。
- 客户端要运行时换步骤实现：不上会怎样——一个 switch 选策略；上了付什么账——继承在编译期把机制钉死，换不了。
- 步骤顺序按变体不同：不上会怎样——两条流程各写一遍；上了付什么账——你必须把 final 骨架开洞， patterns 唯一保证（顺序不变）当场作废。分成两个模板或走组合。
- 一次性脚本／三五个类不再增长：不上会怎样——重复几行；上了付什么账——继承深度 + 算法只能连同子类一起测（非本书）。

## 更省的替代
1. 数据／配置：把步骤做成数组，由固定 runner 顺序执行——`for step in config.steps: step(ctx)`。
   够：步骤同构、只是内容不同。不够：步骤签名不同、需要编译期保证"每步都有实现"。
2. 闭包／函数参数：`sort(items, by: areOrderedBefore)`——一个函数吃一个 closure，通常比抽象类好。
   够：可变的只有一处比较或一次转换、且无共享状态。不够：多处步骤同时变、且共享中间状态。
3. 单个注入对象：把可变步骤打包成一个 `Steps` 协议实现注入。
   够：某一步整块可换、需要运行时替换。不够：那些必须靠继承才拿到的具体共享步骤。
4. 才轮到本模式：骨架必须由**外部掌握调用时机**（框架／父类叫子类），子类只填步骤——这是只有类结构能解决的形状，降级就拿不到"顺序由上而下定死"这一条。

## 最小骨架
**伪代码（角色与方向）**
```
Beverage.prepareRecipe()  # final：骨架在高层，客户端只调它
    boilWater(); brew(); pourInCup(); if wantsCondiments(): addCondiments()
    brew / addCondiments        # 抽象步骤：子类必填，不填不下编译
    wantsCondiments() -> Bool   # hook：默认 true，子类可答可不答
Tea / Coffee：只填 brew + addCondiments
调用方向：Client -> 骨架 -> 子类步骤（上叫下，子类从不反手叫上层）
变化点：步骤实现｜不变点：步骤顺序（final 保证）
```
**Java**
```java
abstract class CaffeineBeverage {
    final void prepareRecipe() {                                   // final：步骤顺序只此一份
        boilWater(); brew(); pourInCup();
        if (wantsCondiments()) addCondiments();                     // hook 决定的可选步骤
    }
    void boilWater() { System.out.println("boil"); }                // 具体步骤：全变体共享
    abstract void brew();                                           // 必经：忘实现过不了编译
    void pourInCup() { System.out.println("pour"); }
    boolean wantsCondiments() { return true; }                      // hook：有默认体，可整体忽略
    void addCondiments() { System.out.println("condiments"); }
}
class Tea extends CaffeineBeverage {
    void brew() { System.out.println("steep tea"); }
    void addCondiments() { System.out.println("lemon"); }
}
class Coffee extends CaffeineBeverage {
    void brew() { System.out.println("drip coffee"); }
    boolean wantsCondiments() { return false; }                        // 只答 hook，不改骨架
}
```
**Swift**
```swift
// ↓↓↓ 配套，不是模式内容
struct Cup { let notes: [String]
    init(_ notes: [String] = []) { self.notes = notes }
    func with(_ s: String) -> Cup { Cup(notes + [s]) } }

protocol BrewSteps {                                      // 必经步骤 = 协议要求：忘实现 = 编译错误
    static func boilWater() -> Cup
    func brew(_ cup: Cup) -> Cup
    func addCondiments(_ cup: Cup) -> Cup
}
extension BrewSteps {                                     // 骨架=扩展里的具体方法，conformer 不提供它
    func prepare() -> Cup {                               // 想彻底封死重写：把骨架包进 final class 里持有步骤
        let poured = pourInCup(brew(Self.boilWater()))
        return condimentsWanted() ? addCondiments(poured) : poured
    }
    func condimentsWanted() -> Bool { true }              // hook：有默认体，可整体忽略
    func pourInCup(_ cup: Cup) -> Cup { cup }             // 具体步骤：全变体共享，可覆盖
    static func boilWater() -> Cup { Cup() }
}
struct Tea: BrewSteps {
    func brew(_ cup: Cup) -> Cup { cup.with("tea") }
    func addCondiments(_ cup: Cup) -> Cup { cup.with("lemon") }
}
```
**TypeScript**
```ts
// ↓↓↓ 配套，不是模式内容
type Cup = { readonly notes: string[] }
const boilWater = (): Cup => ({ notes: [] })
const pour = (c: Cup): Cup => c

type Steps = { brew(c: Cup): Cup; addCondiments(c: Cup): Cup };
function prepareRecipe(s: Steps, wantsCondiments = true) {   // 替代第 2 级：骨架是函数
  const brewed = s.brew(boilWater());
  return wantsCondiments ? s.addCondiments(pour(brewed)) : pour(brewed);
}
abstract class CaffeineBeverage {                   // 才轮到模板方法：时机由框架／父类掌握
  protected abstract brew(c: Cup): Cup;             // 必经：abstract，忘写不过编译
  protected addCondiments(c: Cup): Cup { return c; } // 可选：hook 给默认体
  protected wantsCondiments(): boolean { return true; }
  prepareRecipe(): Cup { return this.brew(boilWater()) }  // 顺序只此一份
}
```
三语分工：Java 段是本书语言的骨架；Swift／TS 段是现代语言映射（非本书）——TS 无 `final`，只能靠不导出＋lint 近似。

## 上了之后要盯的代价
- 必经步骤写成 hook：忘重写不会报错，只会静默半成——hook 的默认体必须等于"合法的什么都不做"。
- 抽象步骤数量：步骤切得越细越灵活、子类越贵；切得粗则反过来。别把每条语句都做成 hook，也别把真在变的步骤并进共享步骤。
- 子类依赖父类已实现的具体步骤，行为测试要连同父类一起跑。
- 骨架是单一爆炸半径：基类改顺序／插一步就是跨层级改动（非本书，本章只点名了这个依赖）。
- 别为了解开一个变体就摘掉 final——那丢掉的是本模式唯一的保证；给那个变体自己的模板或走组合。
- hook 要有理由：每个 hook 只该服务三件事之一——可选步骤、对某步的前后反应、子类替上层做判断；"这里什么都能塞"是模板腐化成 callback 汤的路径。
- 每个 hook 都要付"是否可选"的判定；全抽象子类写不动，全 hook 模板丢编译期约束。
- 语言映射代价：Swift 协议扩展的具体方法可被 conformer 同名实现遮蔽，"不可重排"要靠封装而非关键字（非本书）。

## 形近模式判别
- vs Strategy：变化的是固定序列里的**某一步**，还是可互换的**整个算法**？后者 Strategy；Strategy 的协作对象实现的是全流程，别因为它用了组合就改名叫 Strategy。
- vs Factory Method：可变步骤如果是"造一个对象并返回"，那它就是 Factory Method——模板决定何时要造，子类决定来的是哪个类型。
- 三者一问：Template Method 是子类决定步骤怎么实现；Strategy 是委托决定用哪个行为；Factory Method 是子类决定造哪个具体类。
- 认形状不认教科书：判据是"谁掌握调用顺序"。静态函数、接口驱动、两个方法协作的骨架都算；反过来也别为了图形匹配去加抽象类。

## 组合与框架替身
- 框架的生命周期点就是带 hook 的模板方法：书证是 JFrame 的 update() 算法调 paint() hook、Applet 的 init/start/stop/destroy。做 SDK／基类 controller／运行时且要保证调用次序时，你就是在写模板方法。
- 别逼实现方重写每个生命周期点：默认体／空体 hook 才是框架可被采用的原因。
- 书证里的另外两个非教科书形状：Arrays.sort 建立在 Comparable 上、InputStream.read(byte[],off,len) 建立在抽象 read() 上。
- Hollywood（上层叫下层）解决的是循环依赖与依赖腐化；它不等价于依赖倒置——DIP 说别依赖具体、面向抽象，是更强的通则。拿 Hollywood 当挡箭牌，不豁免你在别处的具体类耦合。
- 现代替身（非本书）：UIViewController 生命周期与 `.task {}`、React 的 componentDidMount／useEffect、Node 中间件管线、Python unittest 的 setUp/tearDown——都已经是你手上的模板方法，直接实现槽位，别手写一层抽象基类去包它们。

## 决策问句
1. 所有变体的步骤**顺序和集合**真的一字不差吗？只要有一个要换序，就别做单一模板。
2. 逐个问每个可变步骤：子类不实现它，还算一个正确完整的子类吗？算 → hook；不算 → 抽象步骤，绝不写成 hook。
3. 有共享中间状态吗？没有的话，一个吃 1-3 个 closure 的函数是不是已经把变化表达完了？
4. 骨架的调用时机由谁掌握？如果是框架／上层，本模式拿得到它该拿的控制权。
5. 客户端要不要运行时换步骤、或整块算法随数据互换？要 → 组合（Strategy），并准备为多出来的对象和一次转付账。

## 证据
源文件：《Head First Design Patterns》1st ed.（Eric Freeman & Elisabeth Freeman, with Kathy Sierra & Bert Bates；O'Reilly, 2004）电子版，第 8 章，书页 pp.275-314。换算：正文 PDF 页 = 书页 + 38。
引用点：p.280-283（收流程＋泛化步骤名、final 骨架）、p.288（得到什么／付出什么）、p.291-295（hook、必经 vs 可选、步骤粒度）、p.296-298（Hollywood 与 DIP）、pp.300-307（callback 版模板、框架实例）、pp.308-311（与 Strategy 对照、bullet 清单）。
标了（非本书）的条目：基类脆弱性（fragile base）这一命名与失效描述；"何时不该用本模式"的汇总判据；最小骨架的 Swift／TS 段与"现代替身"清单（原书只有 Java 示例）。
不可归属项：本章可引证的模板方法只有 Arrays.sort／Comparable、InputStream.read、JFrame.paint、Applet 生命周期；JDBC Template 与 Servlet 例子不在提取文本内，本文不把它们算作本章证据。
