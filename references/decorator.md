# Decorator（中文：装饰者，第 3 章）

## 它吸收什么变化
- 变化轴：**往单个对象上再加一层责任**——加什么、加几层、什么顺序，是每个实例在运行时的决定（调料、缓冲、压缩、日志、加密）。
- 不变的部分：Component 的类型和调用点。装饰后的对象仍能被当作原类型使用；wrapper 与被包对象同类型。
- 搬走的一半：把可选责任从继承体系搬进"持有一个 Component 并委托"的包装类。类型匹配靠继承/实现拿到，新行为靠组合 + 委托拿到（第 3 章隔间对话明确这样分工）。

## 触发信号
- 类名开始枚举组合：`HouseBlendWithMochaAndWhip`（第 3 章爆炸页 p81）→ 每加一种配料或改一次价格就要新类，双份 Mocha 直接没地方放。
- 基类长出可选功能的旗标和方法：`Beverage` 里 `hasWhip()` / `setWhip()`，连 `IcedTea` 也继承到，价格被硬编码在类里（pp.82-84）→ 这是"子类爆炸"的另一种表现，同样是装饰者的靶子。
- 需求句是"这一杯／这个请求／这个用户额外加 X，别的实例不变"→ 责任挂在实例上而不是类型上。
- 看到同型嵌套 `new BufferedInputStream(new FileInputStream(f))`，或某个抽象类名字带 `Filter*` → 库里已经是这个形状，直接顺着它加一层。
- 别人要在**我拥有但不许改**的代码上加行为（框架、SDK、按调料计价的菜单）→ 这是第 3 章给 OCP 定位的实际场景。
- 调用点必须对"叠了什么"一无所知；一旦某处需要 `if (b instanceof HouseBlend)` 才能打折 → 透明性前提已经不成立（见代价一节）。

## 别上的情形
- 组合少、固定、且每种组合在语义上是**不同产品**而不是"加项"：直接子类最诚实；上了＝给不变的东西套层。
- 整个类型统一都有这个行为：子类化；别建一个永远会用的包装。"每个实例恰好被包一次"的那层其实是 Strategy 或子类穿了装饰外衣（这条判据是推广，非本书）。
- 变的是"整段算法换一个"而不是"在同一个算法前后各加一点"：那是 Strategy（第 3 章工具箱把 swap 与 wrap 并列为两个不同答案，pp.105-106）。
- 消费者会做具体类型分派，或调用点需要看链内部：装饰的透明性给不了，硬上只会到处强转。
- 加的东西只是数据（配料价目表）：一个数组 + 一张表更省。
- 上了要付的账：小类海洋、按层增长的实例化代码、更深委托链的调试路径、运行期才暴露的组合错误（第 3 章访谈 p104）。

## 更省的替代
阶梯，从便宜到贵；每级写清什么时候够用、什么时候不够。
1. 数据 / 配置：`beverage.toppings: [Topping]`，`cost = base + Σ prices[topping]`，描述串由数据拼出。够：加项可枚举、彼此无逻辑差异；不够：某层要改写穿过它的数据（压缩、大小写、加密）或自带状态。
2. 一个包装函数（不是类）：`let withLogging = (next: Handler) => (ctx) => { ... }`、Python `functools.wraps` 风格的 `d = fn => args => ...`。够：只有一层、单实例、进出同类型可替换；不够：调用方要按类型长期持有它，或层数会按请求变化。
3. 单个注入协作者（一层包装 + 委托）＝事实上的 Strategy：够——"这个对象总是恰好带这一层"。不够：同类型的不同实例叠不同层、不同顺序。
4. 才轮到链式 Decorator：多责任按实例任意叠加、顺序有意义、调用方保持透明、且底层类不许改。
   只有类结构能解决、不能降级的：需要"同类型 + 委托 + 自带状态"的层，并且扩展者要能在不改 Component 源码的前提下新增一层（OCP 在这里才有实际收益；第 3 章同时警告到处用 OCP 是浪费，pp.86-87）。

## 最小骨架
**伪代码（角色与方向）**
```text
abstract Component { description; cost() }          # 类型契约，所有层同型
class DarkRoast : Component                          # 可被包的底座
abstract Decorator : Component { Component wrapped } # 继承只为拿到类型
class Condiment : Decorator {
    cost() -> wrapped.cost() + myPrice               # 先委托到内层，回来时加钱
    description() -> wrapped.description() + ", Soy" # 串的顺序＝嵌套顺序
}
client: b = Whip(Mocha(Mocha(DarkRoast())))          # 只有最外层是成品
component.method() 沿链向内走 → 再逐层向外返回时补行为
```

**Java**
```java
abstract class Beverage {                                    // Component：类型契约，所有层同型
    String description = "Unknown Beverage";
    String description() { return description; }
    abstract double cost();
}
abstract class CondimentDecorator extends Beverage {          // 装饰器基类：只加，不改被装饰者
    protected final Beverage wrappee;
    CondimentDecorator(Beverage wrappee) { this.wrappee = wrappee; }
    abstract String description();                            // 重新声明＝强迫每一层都重写
}
class Espresso extends Beverage {
    Espresso() { description = "Espresso"; }
    double cost() { return 1.99; }
}
class Whip extends CondimentDecorator {
    Whip(Beverage wrappee) { super(wrappee); }
    String description() { return wrappee.description() + ", Whip"; }
    double cost() { return 0.10 + wrappee.cost(); }            // 委托 + 自己这一层
}
class DecoratorDemo {
    public static void main(String[] args) {
        Beverage b = new Whip(new Espresso());                 // 装饰顺序＝装配顺序，运行时才定
        System.out.println(b.description() + " = " + b.cost());
    }
}
```
**Swift**
```swift
protocol Beverage { var description: String { get }; func cost() -> Double }
struct DarkRoast: Beverage { let description = "Dark Roast"; func cost() -> Double { 2.0 } }

struct Mocha: Beverage {                       // 装饰者：同协议 + 持有同协议
    private let base: any Beverage
    let description: String                    // 由内层字符串拼出：顺序即结果
    init(_ base: any Beverage) { self.base = base; description = base.description + ", Mocha" }
    func cost() -> Double { base.cost() + 0.50 }   // 委托向内，返回时加值
}
let cup: any Beverage = Mocha(Mocha(DarkRoast()))  // 保留的是最外层，不是中间层
```
**TypeScript**
```ts
interface Beverage { readonly description: string; cost(): number }
const darkRoast = (): Beverage => ({ description: "Dark Roast", cost: () => 2 });
// 一层时函数包装即可；需要按实例叠多层时才用同型装饰链
const mocha = (b: Beverage): Beverage => ({
  description: `${b.description}, Mocha`,        // 顺序影响可见字符串
  cost: () => b.cost() + 0.5,                    // 委托内层，回来后加
});
const whip = (b: Beverage): Beverage => ({ description: `${b.description}, Whip`, cost: () => b.cost() + 0.4 });
let cup: Beverage = whip(mocha(mocha(darkRoast())));   // 最外层才是成品
```

## 上了之后要盯的代价
- **具体类型分派在包装下断掉**（第 3 章点名的第一个破损）：`if HouseBlend 就打折` 这类代码一旦被包，最外层是装饰者而不是 HouseBlend，判断静默失效；第 3 章访谈把"依赖具体组件类型"列为头号抱怨（p99、p104）。透明性只在所有人都对抽象 Component 编码时成立。
- **透过链偷看＝越过意图**（第二个 named 破损）：外层装饰者要去读改内层（把 "Mocha, Whip, Mocha" 改写成 "Whip, Double Mocha"）就不是装饰者该做的事；书给的合法出口是①再加一个后处理装饰者改写最终描述串，②让 `getDescription()` 返回集合。把可变列表穿过各构造器当暗道，会让所有装饰者互相耦合、失去独立增删。
- **链越长，账越贵**：设计里塞满只加一点东西的小类，实例化代码随每层增长，出错概率随之上升；java.io 出名地难读就是这笔账（p101、p104）。
- **身份与相等性**：包装不是被包装的那个对象——`equals` / `hashCode`、Map/Set 的键、序列化类型标签都会跟着变；需要一致就得显式委托相等性，并把建链收进工厂（第 3 章未展开，非本书）。
- **调试路径变深**：一次 `cost()` / `read()` 要沿嵌套委托走到内层再逐层折回；栈帧与对象图都变长。
- **覆盖不全＝静默绕过**：Component 有多个入口时（单字节 `read()` 与字节数组 `read()`），装饰者必须把整张表面都委托；漏一个方法，那条路径就绕过装饰（第 3 章 `LowerCaseInputStream`，pp.102-103）。别自动覆盖 API 刻意留裸的路径（如 mark/reset 类），逐方法核实（这条细化的告诫属外推，非本书）。
- **顺序耦合**：装饰顺序就是行为顺序——每层都在"委托前/委托后"动手（要点 p90）；纯加算层（调料加钱）对顺序不敏感，但转换数据的层先压缩后加密 ≠ 先加密后压缩（后半句是推广，非本书）。别为了排版随手重排链。
- **拿错引用**：建链时必须把最外层当返回值；留着中间层引用＝静默丢掉所有外层（p98、p99）。

## 形近模式判别
- Strategy vs Decorator：整段算法换一个（兄弟互换）还是同一个算法前后各加一点、按实例叠？判据："把这层删掉原对象还完整吗"——完整＝装饰，残缺＝策略。
- 子类 vs Decorator：这个行为是类型级的（人人如此）还是实例级的（这杯才有）？第 3 章 p85 的核心对立就是这个。
- Adapter vs Decorator（第 7 章，本文件未取证）：Adapter 改接口形状让不兼容能接上，Decorator 保持同类型只加责任（非本书）。
- Observer vs Decorator：加"被告知的人"用注册，加"这杯的责任"用包装；两者都能满足 OCP，挑便宜的那个。

## 组合与框架替身
- 规范真实样本 java.io（pp.100-101）：`InputStream` 抽象组件，`FileInputStream` / `ByteArrayInputStream` 具体组件，`FilterInputStream` 抽象装饰者，`Buffered` / `LineNumber` / `Data` / `PushbackInputStream` 具体装饰者；`Reader` / `Writer` 家族同构复制一遍。新能力＝一个新装饰者，而不是新的组合子类。
- 与创建型配对：链超过两三层的构造代码该收进工厂或 builder——第 3 章访谈自己把这一步推给后续模式（p104）。
- 与 OCP 配对：注册点（Observer）与包装链（Decorator）都实现"不改源码加行为"；只在最可能变的那一侧花力气（pp.86-87）。
- 抽象类还是接口当 Component：模式传统要抽象 Component；第 3 章为了不改动已有 `Beverage` 而复用它，不为模式纯度重写（p93）；"新代码更常上接口以免烧掉单继承名额"属推广，非本书。
- 现代同族形状：Python `io.BufferedReader(FileIO(...))`、Node 的 `app.use` 中间件栈与 Transform 流、gRPC interceptor、React HOC、Redux store enhancer（第 3 章只到 java.io 与 Servlet 主题，其余非本书）。
- Servlet filter 装饰响应输出流：确属本章主题，但取证页在提取范围之外（非本书）。

## 决策问句
1. 这个责任是"实例级、按次点单"还是"类型级、人人如此"？只有前者值得装饰。
2. 有没有任何调用点在测试或强转具体组件类型？有一个就先修它，否则透明性只是嘴上说说。
3. 装饰者需不需要知道链上还有哪些别的层？需要 → 设计错了，改成后处理装饰者或让接口返回集合。
4. 链有几层？超过 3 层时，构造复杂度和调试成本由谁承担，能不能折成一个类或用数据表替掉？
5. Component 一共有几个入口方法？每一个都被委托了吗？（漏一个就是绕过装饰的暗道）

## 证据
- 源文件：《Head First Design Patterns》1st ed.（Eric Freeman & Elisabeth Freeman, with Kathy Sierra & Bert Bates；O'Reilly, 2004）电子版，第 3 章，书页 pp.79-108。换算：正文 PDF 页 = 书页 + 38。
- 本书依据：Starbuzz 原类图 p.80、子类爆炸 p.81、`Beverage` 旗标污染与硬编码价 pp.82-84；静态继承 vs 运行期组合 master/student p.85；OCP 及"到处用是浪费""通常你做不到" pp.86-87；"把装饰者想成 wrapper" p.88；模式类图与"委托前/后加行为"要点 p.90；`CondimentDecorator` 代码 pp.92-95；隔间对话（接口 vs 复用已有抽象类）p.93；`StarbuzzCoffee` 建链与双份 Mocha p.98；p99 四问（最外层引用、装饰者能否互相知道、按 HouseBlend 判断、size 装饰者）；java.io 图与讲解 pp.100-101；`FilterInputStream` 覆写 `read()` pp.102-103、`InputTest` p.103；"Confessions of a Decorator"（小类海洋、实例化复杂、具体类型抱怨）p.104；工具箱页 Strategy 与 Decorator 并列 pp.105-106；Soy/双份 Mocha 解答 pp.106-108。
- 标了（非本书）的条目：转换层的顺序敏感（先压缩后加密 vs 先加密后压缩）；包装影响 `equals` / `hashCode` / Map 键与"显式委托相等性 + 工厂统一建链"的处方；"恰好一层的包装其实是 Strategy 或子类"这条判据及其措辞；`FilterInputStream` 之外关于刻意留裸路径的细化告诫；Adapter 对照；"新代码优先接口"的后半句；Servlet 输出流装饰（主题在范围内、取证页不在）；java.io 之外的现代替身（Node 中间件、Transform 流、HOC、Python io、gRPC interceptor）；Swift/TS 代码骨架。
- 本文件不主张：性能数字、语言级反射装饰器语法、响应流之外的并发语义——均不在取证范围内。
