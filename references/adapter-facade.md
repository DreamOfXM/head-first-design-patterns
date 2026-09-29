# Adapter & Facade（中文：适配器与外观，第 7 章）

## 它吸收什么变化
- Adapter 吸收的是**接口形状不一致**：客户端已经按 Target 写死了，Adaptee（vendor SDK / 遗留模块）的名字、参数个数、单位都对不上。变化点 = 外部契约，不变 = 客户端调用形状（p.275-276 / p.279）。
- Facade 吸收的是**调用顺序与部件数量**：一个用例要跨 8-13 个类按序调一遍。变化点 = 子系统内部构成，不变 = 客户端想要的高层目标（p.294-297 / p.302）。
- 两者都是包装；搬走的都是"让客户端自己去学另一套 vocabulary"，但方向不同：Adapter 迁就**已有**契约，Facade 允许你**新定义**契约。

## 触发信号
- vendor / 遗留类的 `gobble()` 对上你已有的 `quack()`：名字、arity、单位不匹配，而调用点已经存在 → Adapter（Target/Adaptee 三个角色先定下来再写代码）。
- 两个团队、一个不能改的稳定代码库、一个外部库契约不同 → 把适配器放在**不能被改的那一侧**；最好由 vendor/子系统方自己出货适配器，否则一个外部边界一个适配器类，别处不许碰这条边界（p.275 / p.281）。
- Target 有 40 个方法但客户端只用 6 个 → 仍然要做，但先数真实用量（p.280 FAQ：工作量与要满足的接口面积成正比）。
- Target 里有 Adaptee 根本没有的操作（如 `Enumeration` 之上实现 `Iterator.remove()`）→ 显式抛不支持，不要静默（p.288）。
- 适配器需要循环、重试、截断、抽样才能把签名对齐（`fly()` 变 5 次 `fly()`）→ 你适配的是**行为**不只是签名，必须把这个代价写可见（p.277 / p.310）。
- 同一个用例的顺序调用在多处重复抄写，新调用方一上手就要学 5 个部件 → Facade。
- `station.getThermometer().getTemperature()` 这类链在业务逻辑里被 grep 到 → 最小知识原则/target 提方法，不是提 getter（p.303-305）。
- 半套系统按接口 A 写、半套按接口 B 写（同一能力）→ 双向适配器，**只在迁移期**（p.280 FAQ / p.289）。
- 测试脚手架和 App 各自重复同一套部件的构造顺序才敢调用 → Facade 顺势当**装配/bootstrap 层**：在入口构造好、把现成的外观交给调用方，别要每个客户端自己拼部件（p.299-301）。

## 别上的情形
- 调用点只有一两处、且你能改调用方：直接改成原生形状更便宜。上适配器付什么账：一个永久的翻译层，将来没人记得为什么存在。
- 用 Facade 去满足一个客户端已经写死的契约：不上只是换个包装方向；上了会直接破坏调用方 —— 那是 Adapter 的活。
- 用 Adapter 去做你其实能定义接口的场景：不上只是多写几个调用；上了你把复杂度原样搬了个家，还多了个翻译层要维护。
- 每个方法都只是单次委托、类名重复它包的那个模块 → facade fever，不上什么也不丢；上了白付一层间接、一个额外要改的地方，耦合没降（p.298 / p.305 的成本口径；"简单内聚模块不需要"这条，非本书）。
- 为了给 `console.log` / `print` / `System.out.println` 也"守规矩"而造 pass-through 包装：本章自己承认这类调用违反最小知识，并明说没有原则是法律（p.305 FAQ / p.306）。只在**变化会级联**的地方减依赖。
- 已经第三代包装叠在同一个上游上：别再加第四个。收敛到"一条边界一个 Target"，删掉最后一批遗留调用点后连适配器一起删（p.280 的警告；"适配器考古学"这个失效模式，非本书）。
- 把子系统的业务逻辑搬进 Facade，或让一个 Facade 服务所有消费者 → 它会变成 god object；同一子系统允许多个 Facade（p.297-298）。

## 更省的替代
阶梯，从最便宜的开始：
1. **数据 / 配置**：字段名与单位映射写进一张表，别为它建类。`const DTO_TO_DOMAIN = { createdAt: 'ts', uid: 'id' }`；REST 子集用配置挑字段。
2. **函数 / 闭包**：一个纯映射函数就是对象适配器。TS `const asDuck = (t: Turkey): Duck => ({ quack: () => t.gobble(), fly: () => repeat(5, t.fly) })`；Swift 一个返回协议值的工厂函数；Python 模块级函数绑住 legacy client。
3. **单个注入对象 / 一个模块**：`api/` 一个模块导出 Target 形状，组件只 import 类型不 import raw client；Facade 常常就是这个模块本身，不需要再包一层类（`toDomain(dto)` 是适配器，`api/` 模块是外观）。
4. **才轮到类结构**：需要在**多条**调用点上保持同一个已写死的契约、要能力旗标与诚实的不支持路径、或要做分层 Facade（Facade 组合 Facade，p.307）时，才要一个真正的类型。
不能降级的理由：Target 需要被多处**以同一身份**依赖（含 `instanceof`/conformance 检查、可被替换的注入位、需要抛不支持并带能力标记）时，纯函数没有可依赖的名字与类型；这时适配器/外观必须是一个类型。
遗留改造的顺序（比再造一层更省）：**边缘适配、核心做外观** —— 先用今天的用例语言给旧子系统包一个 Facade 当长期契约，再给没迁完的调用点挂适配器，流量排干后删适配器（p.286-290 的双向迁移 / strangler 口径）。

## 最小骨架
**伪代码（角色与方向）**
```
Client ──只认──▶ Target（interface/protocol）        ← 不能被改的那一侧
Adapter ──实现──▶ Target ；──持有──▶ Adaptee（vendor/legacy）  ← 组合，不是继承
Adapter 的方法 = 委托 + 翻译；做不到的操作 抛 unsupported
Facade ──持有──▶ {部件A,部件B,部件C…} ；──提供──▶ watchMovie() / endMovie()  ← 目标级动词
```
**Java**
```java
interface Duck { void quack(); void fly(); }                       // Target：不能被改的那一侧
class Turkey { void gobble() {} void fly() {} }                     // Adaptee：接口不兼容，不改它
class TurkeyAdapter implements Duck {                               // 对象适配器：组合一个 Adaptee 到底
    private final Turkey turkey;
    TurkeyAdapter(Turkey turkey) { this.turkey = turkey; }
    public void quack() { turkey.gobble(); }                        // 委托 + 翻译
    public void fly() { for (int i = 0; i < 5; i++) turkey.fly(); }  // 代价写在这里，别再藏
}
class EnumerationIterator implements java.util.Iterator<Object> {   // 旧接口适配成新接口
    private final java.util.Enumeration<Object> source;
    EnumerationIterator(java.util.Enumeration<Object> source) { this.source = source; }
    public boolean hasNext() { return source.hasMoreElements(); }
    public Object next() { return source.nextElement(); }
    public void remove() { throw new UnsupportedOperationException("read-only Enumeration"); }  // 做不到的响亮失败
}
class Amplifier { void on() {} void off() {} }
class Projector { void on() {} }
class HomeTheater {                                                 // Facade：持有部件，给目标级动词
    private final Amplifier amp = new Amplifier();
    private final Projector projector = new Projector();
    void watchMovie() { amp.on(); projector.on(); }
    void endMovie() { amp.off(); }
}
```
**Swift**
```swift
// ↓↓↓ 配套（vendor / legacy 侧），不是模式内容
struct Turkey { func gobble() {}; func fly() {} }        // Adaptee：接口不兼容的原对象
struct Amp { func on() {}; func off() {} }; struct Screen { func down() {} }; struct Player { func play() {} }

protocol Duck { func quack(); func fly() }               // Target
struct TurkeyAdapter: Duck { let turkey: Turkey           // 组合：一个对象包到底
    func quack() { turkey.gobble() }
    func fly() { for _ in 0..<5 { turkey.fly() } }        // 代价写在这里，别再藏
}
final class HomeTheater {                                 // Facade：持有部件，给目标级动词
    let amp: Amp; let screen: Screen; let player: Player
    init(amp: Amp, screen: Screen, player: Player) { self.amp = amp; self.screen = screen; self.player = player }
    func watchMovie() { amp.on(); screen.down(); player.play() }
    func endMovie() { amp.off() }
}
let duck: Duck = TurkeyAdapter(turkey: Turkey())          // 调用点只认 Target，换 vendor 不改这里
```
**TypeScript**
```ts
// ↓↓↓ 配套，不是模式内容
type Turkey = { gobble(): void; fly(): void }            // Adaptee：厂商形状，不改它
interface Enumeration<T> { hasMore(): boolean; next(): T }   // 旧接口，没有 remove()
type Deps = { amp: { on(): void } }
const seq = (d: Deps) => { d.amp.on() }

interface Duck { quack(): void; fly(): void }             // Target 留在自己的模块
const asDuck = (t: Turkey): Duck => ({                    // 对象适配器：闭包足够
  quack: () => t.gobble(),
  fly: () => { for (let i = 0; i < 5; i++) t.fly() },
});
class EnumerationIterator implements Enumeration<unknown> {
  hasMore() { return false }
  next(): never { throw new Error('unsupported: read-only Enumeration') }  // 响亮地失败
}
export const createPlayer = (d: Deps) => ({ watchMovie: () => seq(d) })  // 外观 = 装配层
```

## 上了之后要盯的代价
- 成本与 Target 面积成正比：先数真实用到的方法，再决定是"窄 Target + 文档化的缺口"还是"迁就几个调用点更便宜"（p.280）。
- 不支持的操作必须响亮失败：`UnsupportedOperationException` / `NotImplementedError` / 501；返回 `null`/`[]`/`false` 会让调用方静默丢掉一次 mutation，几周后才发现（p.288-290）。
- 便宜的签名可能藏着 N 次底层调用：一个"看起来免费"的接口方法变成 N 次网络往返，调用方的性能模型就成了谎话。方法名或注释里暴露代价，或改成 bulk 接口（p.277 / p.310；N+1 的表述，非本书）。
- 类适配器在 Java/Swift/Kotlin/TS 里做不了：它需要多继承才能同时拿到 Target 与 Adaptee。Swift 里"一个基类 + 一个协议"勉强能拼但比组合脆；Python 能做却因 MRO 让组合更安全。C++ 才是经典场景（p.282-284 / p.285）。
- 别把 adaptee 的行为抄进适配器：那是委托变分叉，从此 vendor 每次升级你都要重做。
- Facade 简化但**不封装**：子系统类仍然公开可直用，它是好走一点的门不是墙。要清楚这不是访问控制；升级子系统时只改 Facade，但迁移中途别让客户端绕过它（p.297-298）。
- 最小知识按字面遵守的账：转发方法与包装类增多、复杂度与开发时间上升、运行时性能下降，最后你连标准库都要包。本章把它列为"何时何地有用"而非定律（p.305-306）。
- 提取一个仍然调用被返回对象的 private helper，依赖没变，违规也没修好（p.306 / p.310 练习的结论）。

## 形近模式判别
- Adapter vs Facade：决定性问题 —— **你欠客户端的是什么形状**。客户端已按某个既有契约写死 → Adapter（换形状）；客户端只是面对太多活动部件、形状可由你定 → Facade（新造更高层接口）（p.298 FAQ / p.308）。
- Adapter vs Decorator：都包装。Decorator 保持同一接口并加责任，Adapter 换掉接口（p.290-291 / p.292）。决定性问题 —— **客户端看到的类型变了没有**。
- Facade vs 外观型 Singleton：装配层不该是 `static let shared`；构造它并注入（p.299-301 的构造注入 + 现代判断）。
- Facade vs 反腐蚀层/网关：跨边界、把外部 vocabulary 翻译成本域概念是 adapter 类工作；同一系统内给用例提供入口是 Facade。
- 三个都"包一层"，别按类图相似度选模式，按**意图**命名（`*Adapter` / `*Decorator` / `api/` 模块）（p.292 / p.298）。

## 组合与框架替身
- 常与 Iterator/Enumeration 迁移、Command（把 vendor 调用包成命令值）、Facade + Adapter 组合（外观做长期契约、适配器做迁移期尾巴）搭配。
- 分层 Facade：Facade 组合 Facade，但客户端仍可直接用部件（p.307）。
- 现代替身（非本书）：后端 anti-corruption layer / `compat/` 包 = 对象适配器；gRPC gateway 把 stub 映射到领域类型；BFF 就是一个 per-client Facade；`toDomain(dto)` mapper 模块、`Pick<Target, UsedKeys>` 子集适配 = 闭包/函数式适配器；barrel export（`facade.ts`）默认导出装配层但不禁止深导入；`Object.assign` 合并两个映射视图 = 双向适配器的迁移期形态。有现成的映射层/网关就用，别手写第四代包装。

## 决策问句
1. 哪一侧**不能改**？把适配器贴到那一侧的接口上；如果两侧都能改，先问要不要迁移而不是包装。
2. 客户端真正用到 Target 的几个方法？其余是抛不支持还是拆一个更窄的协议？
3. 有没有哪个"方法"其实要做多次底层调用？它的代价在名字/文档/测试里看得见吗？
4. 这个包装类是不是每个方法都只委托一次、名字重复被包模块？是 → 删掉，用函数或模块级 API。
5. 是在**简化**（新调用方太多部件）还是在**迁就**（老调用方契约已写死）？答错这题，模式就选错了。

## 证据
- 源文件：《Head First Design Patterns》1st ed.（Eric Freeman & Elisabeth Freeman, with Kathy Sierra & Bert Bates；O'Reilly, 2004）电子版，第 7 章，书页 pp.235-274。换算：正文 PDF 页 = 书页 + 38。
- 书页区间：现有系统 vs 不匹配 vendor p.275-276；`TurkeyAdapter.fly()` 五次 p.277；三角色图与定义 p.279、p.281；FAQ（工作量与接口成正比、新旧共存/双向适配器、混用会混乱）p.280；对象 vs 类适配器 p.281-285（"Java 里做不到"p.282-284、face-off p.285）；遗留迁移双向 p.286-290（`EnumerationIterator.remove()` p.288、Iterator/Enumeration 方向 p.289-290）；Decorator vs Adapter p.290-292；HomeTheater 13 步到一次调用 p.294-297、构造与装配 p.299-301；定义与 FAQ p.302（不封装、多个 Facade）、分层 p.307、要点 p.308；最小知识 p.303-306（四类允许被调对象、Car 例、"没有原则是法律"、`System.out.println` 自认违规）、练习结论 p.306 / p.310；`DuckAdapter.fly()` 随机 p.310。
- 标了（非本书）的条目：适配器叠成考古学的失效模式、"简单内聚模块不需要 Facade / facade fever"这一判据、N+1 与批量接口的表述、以及全部现代替身（anti-corruption layer、BFF、gRPC gateway、`Pick` 子集适配、barrel export、`asDuck` 闭包适配器、Swift 单继承现实与 Python MRO）。
- 上述两类内容均可回指 distill 中对应 `INFERRED: yes` 行或本书未涉及的现代写法。
