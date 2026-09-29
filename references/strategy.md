# Strategy（中文：策略，第 1 章）

## 它吸收什么变化
- 变化轴：同一件事"怎么做"有多个可互换实现（fly / quack / 武器 / 按州收销售税 / 计价 / 排序 / 校验），选哪个是运行期的决定。
- 不变的部分：宿主的身份、共享状态和其余方法。第 1 章最终结构里 `Duck` 仍是超类，`swim()` 继续被继承，`display()` 继续留在抽象层。
- 搬走的一半：只把真正在变的那一个行为抽成"一个超类型 + N 个实现"，宿主 HAS-A 一个协作者并委托调用。只搬 fly/quack，不搬 display/swim。

## 触发信号
- 继承异味清单（第 1 章 "Sharpen your pencil" A–F）四条同时看见两条以上就该停手判：① 多个子类把同一方法重写成空实现或近似副本 → 行为站错了地方；② 运行期改不了行为 → 缺一个可换的缝；③ 没有一处能看出"哪个类型做什么" → 行为散在树里；④ 改基类会误伤兄弟子类 → 继承在放大副作用。
- 往共享基类加一个方法，不相干的子类也获得了它（第 1 章橡皮鸭：给 `Duck` 加 `fly()` 就得到会飞的橡皮鸭）→ "局部改动引发非局部副作用"，该行为该独立成单元。
- 需求句形如 "each X uses one of these at a time and may switch"，或出现 per-user / per-tenant / toggleable → 命中"运行时可换"判据（setter 缝）。
- 能力接口满天飞、每个实现类各自复制同一段方法体（第 1 章：48 个会飞的 Duck 子类必须一起改）→ 标记接口拿复用换类型正确性；只在"能力是稳定的类型事实且没有实现可共享"时才成立（把它推广到一般能力接口属外推，非本书）。
- 宿主里出现按类型分支的 if/switch 来挑算法（第 1 章 Character/Weapon 谜题：`WeaponBehavior` 族 + `setWeapon()`）→ 那张分支表就是没被抽出来的策略族。
- 变体维度不是域名词（税规则、验证器、渲染器）→ 策略的形状不要求它是"东西"（第 1 章 NNDQ 正面承认"只是行为"的类合法）。

## 别上的情形
- 只有一个实现、且看不见第二个：不上＝少一个接口和一个跳板；上了＝阅读时的间接层与多出来要记住的类型（Pattern Fever；第 1 章自己的诊断是"在 Hello-World 大小的问题上用模式"，而"单实现/没人调的 setter 就是过热信号、等第二个变体再抽"属外推，非本书）。
- 变的是类型身份而不是做法（每种 X 天生不同，且共享大量字段）：继承或数据驱动配置更清楚；硬上策略＝对象数量和连线一起涨。
- 变体之间只是数值/表项差异（税率表、折扣表）：一张表或一个枚举就够，抽策略类是把数据伪装成类型。
- 宿主本身是一组无共享状态的纯计算：策略退化成一个函数参数（第 1 章仍是类结构；"无状态就用函数更省"是本书未讲的现代判断，非本书）。
- 别顺手把没在变的也搬走：`display()` / `swim()` 一起抽走只会白增结构，第 1 章明确只动 fly/quack。
- 别为"鸭子不能跳舞""鸭子不能又飞又叫"重构：这两条不是继承问题（第 1 章叙事支持此排除，但答案页未印，判据属外推，非本书）。

## 更省的替代
阶梯，从便宜到贵；每级写清什么时候够用、什么时候不够。
1. 数据 / 配置：`taxRates: [State: Rate]`、枚举 + 查表；一次变化＝改数据而不是改调用方。够：变体只是参数或数值差异、逻辑同构；不够：变体各自要带依赖、状态或多步进出错流程。
2. 函数 / 闭包参数（非本书；第 1 章仍是类结构）：`perform(fly: () -> Void)`、`sort(by: comparator)`、把 `weapon: { use(): void }` 放进 props。够：算法无状态、纯计算，捕获即完成注入；不够：一族实现各自带状态与生命周期（第 1 章 NNDQ 承认行为类可以合法持有振翅频率、飞行上限这类属性，此时才需要"类"）。
3. 单个注入协作者、不抽超类型：宿主持有一个具体协作者，由装配处传入。够：调用方不需要对超类型编程、换实现只发生在装配处；不够：调用方必须不知道具体类型，或同一实例运行期要换。
4. 才轮到 Strategy：≥2 个真实现 + 运行期选择 + 调用方只对超类型编程。只有类结构能解决的是"策略自带状态且要多态携带"——降级成函数会丢状态与依赖，降级成配置表会丢行为。

## 最小骨架
**伪代码（角色与方向）**
```text
protocol FlyBehavior { fly() }              # 变化轴：一个行为一个超类型
protocol QuackBehavior { quack() }
class Duck {                                # 宿主：不变的部分留在这里
    var fly: FlyBehavior                    # HAS-A，声明成超类型而非具体类
    performFly() -> fly.fly()               # 委托；这一行才是变化点
    setFlyBehavior(fb) -> fly = fb          # 运行时可换的缝
}
client: duck.fly = FlyRocketPowered()       # 绑定发生在运行处
new Duck(fly: FlyWithWings())               # 构造处写死＝第 1 章承认的债
```

**Java**
```java
interface FlyBehavior { void fly(); }                       // 一个行为一个超类型＝一条变化轴
class FlyWithWings implements FlyBehavior { public void fly() { System.out.println("wings"); } }
class FlyRocketPowered implements FlyBehavior { public void fly() { System.out.println("rocket"); } }
class Duck {
    private FlyBehavior flyBehavior;                        // HAS-A：声明成超类型，不是具体类
    private final String name;                              // 不变部分（共享状态）留在宿主
    Duck(String name, FlyBehavior flyBehavior) { this.name = name; this.flyBehavior = flyBehavior; }
    void performFly() { flyBehavior.fly(); }                // 委托：这一行才是变化点
    void setFlyBehavior(FlyBehavior fb) { this.flyBehavior = fb; }   // 运行时可换的缝
    String name() { return name; }
}
class StrategyDemo {
    public static void main(String[] args) {
        Duck d = new Duck("Mallard", new FlyWithWings());    // 构造处写死＝第 1 章承认的债
        d.setFlyBehavior(new FlyRocketPowered());            // 不重建宿主就换算法
        d.performFly();
    }
}
```
**Swift**
```swift
protocol FlyBehavior { func fly() }
struct FlyWithWings: FlyBehavior { func fly() { print("wings") } }
struct FlyRocketPowered: FlyBehavior { func fly() { print("rocket") } }

final class Duck {
    var fly: FlyBehavior                            // 持有超类型，不是具体 struct
    let name: String                                // 不变部分（共享状态）留在宿主
    init(name: String, fly: FlyBehavior) { self.name = name; self.fly = fly }
    func performFly() { fly.fly() }                 // 委托点＝变化点
    func setFlyBehavior(_ fb: FlyBehavior) { fly = fb }  // 运行时缝
}
let d = Duck(name: "Mallard", fly: FlyWithWings())
d.setFlyBehavior(FlyRocketPowered())                // 不重建宿主就换算法
```
**TypeScript**
```ts
// ↓↓↓ 配套，不是模式内容
const log = (s: string) => { void s }                    // 装配处才 import 具体实现

type FlyBehavior = () => void;                          // 无状态时，函数就是策略
interface WeaponBehavior { use(): void }                // 带状态/多方法才要对象

class Character {
  constructor(private weapon: WeaponBehavior, private fly: FlyBehavior) {}
  setWeapon(w: WeaponBehavior) { this.weapon = w }      // 换协作者，不换子类
  fight() { this.weapon.use(); this.fly() }             // 委托：调用方不知具体类型
}
const c = new Character({ use: () => log("sword") }, () => log("jump"));
c.setWeapon({ use: () => log("bow") });                 // 具体选择留在装配处
```

## 上了之后要盯的代价
- 类型账与跳板账：1 个超类型 + N 个实现 + 宿主字段，每次调用多一层跳转（第 1 章只讲收益，这条成本与"单实现阈值"是外推，非本书）。
- setter 缝换来运行期可换，代价是对象可变、可能处在半配置状态；类型固定就构造期设好，别公开 setter（非本书）。
- 宿主委托方法随行为数量线性膨胀：每个行为一个 pass-through，读代码的人要跨文件才知"到底怎么飞"。
- 抽象泄漏会被评审质疑：策略类"不是名词"（第 1 章 NNDQ 已答：行为类合法，且可自带状态；但别把宿主身份偷偷塞回行为对象）。
- 构造期写死具体实现＝债留在原地：第 1 章自己承认初始化方式不灵活，把这件事交给后续创建型模式，别停在策略上就宣称完全灵活。
- 组合替代继承的通用付款：多了对象与连线，失去"一处定义"的直觉；真正的共享状态/身份仍该用继承（成本的枚举属外推，非本书）。

## 形近模式判别
- 子类覆盖 vs Strategy：这个选择在编译期被类型定死，还是要按实例/请求运行期变？只有后者值得抽缝。
- 标记接口（Flyable/Quackable）vs Strategy：接口后面有没有要共享的实现？没有＝类型事实用标记接口；有＝策略族，否则同一段方法体被复制 N 份。
- State vs Strategy（State 在第 10 章，本文件未取证）：谁在换它——外部挑选算法是 Strategy，对象随自身内部状态迁移是 State（非本书）。
- Template Method vs Strategy（第 8 章，本文件未取证）：流程骨架换不掉、只换其中一步时先考虑模板方法（非本书）。

## 组合与框架替身
- 与创建型模式配对：谁 new 具体策略是第 1 章留下的缺口；把"选哪个、何时建"收进工厂或注册表后，宿主仍只对超类型编程。
- 与配置/数据层配对：需求写"按州、按用户档级"时，解析点在装配/请求入口，而不是宿主内部（第 1 章销售税例子就是按州取策略）。
- Swift：协议 + 值类型实现；带关联数据的枚举常常比"一个武器一个类"更省（非本书）。
- TypeScript/React：策略通常是 prop 或 context 里的函数值，换策略＝一次 setState，不需要 setter 方法（非本书）。
- Node/Python：`dict[str, Callable]` 注册表按数据（州码、档级）解析，替掉宿主里的 if 链；现成形状如 `Array.prototype.sort(comparator)`、格式化/排序/校验注入位（非本书）。

## 决策问句
1. 这个行为现在真有两个以上实现，还是我预感会有？预感不算触发信号。
2. 选择发生在编译期（按类型）还是运行期（按实例/请求/租户）？只有后者需要可换的缝。
3. 变体之间的差异是数据、纯计算还是带状态的逻辑？分别对应表、函数参数、策略类。
4. 搬走它之后宿主还剩什么没搬？没搬的是不是本来就不该搬（`swim()` / `display()` 就是答案）？
5. 谁决定初始实现？如果答案是"构造函数里写死"，这笔债现在归谁，要不要现在就交给创建型模式？

## 证据
- 源文件：《Head First Design Patterns》1st ed.（Eric Freeman & Elisabeth Freeman, with Kathy Sierra & Bert Bates；O'Reilly, 2004）电子版，第 1 章，书页 pp.1-36（另含前言，按 PDF 页 pp.27-38 读，前言不套 +38）。换算：正文 PDF 页 = 书页 + 38。
- 本书依据（按块）：策略正式定义与"行为族/按州销售税"（"The Big Picture on encapsulated behaviors" + 定义页）；Character/WeaponBehavior 谜题与解（含 `setWeapon()`）；运行期换行为（"Setting behavior dynamically"：ModelDuck 先落地、装 RocketFly 后输出变化）；只搬 fly/quack、display 留抽象、swim 留继承（"Zeroing in on the problem" + 分离变化轴原则页）；构造期写死具体行为是承认的债（书页 p17）；行为类合法且可自带状态（NNDQ "a class that's just a behavior"）；宿主保持抽象类以复用共享状态与 swim（NNDQ "Should we make Duck an interface too?"）；往基类加方法放大副作用（橡皮鸭 "a localized update caused a non-local side effect"）；标记接口毁掉复用与 48 个子类一起改（"How about an interface?"）；继承异味清单（"Sharpen your pencil" A–F 及其答案页复现）；Pattern Fever（第 1 章 Observer 对话）。
- 标了（非本书）的条目：额外间接跳板与"单实现就别上"阈值、"等第二个变体再抽"；setter 带来的可变/半配置代价；无状态策略用函数/闭包参数更省；把标记接口结论推广到一般能力接口；"不能跳舞/不能又飞又唱不算真继承问题"；State 与 Template Method 的对照；Swift/TS/Node/Python 的语言形状与框架替身；组合代价的枚举。
- 本文件不主张：OCP 术语（第 1 章只描述了效果、未命名该原则）、模式分类目录、并发与测试策略——均未在取证范围内。
