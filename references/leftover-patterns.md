# Leftover Patterns（中文：附录速查九模式）

九个「真模式但少见」的目录级条目：Bridge、Builder、Chain of Responsibility、Flyweight、Interpreter、Mediator、Memento、Prototype、Visitor。附录每个模式只给了半页场景 + 一图 + 优缺点（distill 标 `DEPTH: catalog`，书自己只勾了轮廓），所以每块只有三行：吸收什么变化 / 触发信号 / 更省的替代。形近判别集中在「形近模式判别」，代价集中在「上了之后要盯的代价」。骨架只给共同形状、不给九份实现代码——在目录深度上写骨架会把没验证过的细节写成结论。

## 它吸收什么变化

按变化轴分组：创建类（Builder 吸收「装配步骤与合法组合」的变、Prototype 吸收「造哪个具体类」的变）；实例与历史类（Flyweight 吸收「有多少个逻辑实例」、Memento 吸收「回到哪一份状态」）；结构类（Bridge 吸收「抽象与实现各自演化」、Visitor 吸收「要做什么操作」）；通信类（CoR 吸收「谁接手」、Mediator 吸收「协调规则归谁」）；语言类（Interpreter 吸收「规则怎么解释」）。不变的那一半通常是产品/结构本身；搬走的是「步骤、数量、接手者、操作」这类知识住在哪儿。

## 触发信号

总判据：说不出「数量 / 创建 / 历史 / 接手者 / 协调规则 / 操作 / 装配步骤 / 两边各自演化」这八种压力里的哪一种正落在你身上，就还没到选这九个的时候。逐模式信号见各自小节的 **触发信号** 行。

## Bridge

**它吸收什么变化**：抽象侧（RemoteControl）与实现侧（TV、Sony、RCA）各自独立演化；抽象侧每个方法只对着实现接口写，具体子类 extends 抽象侧，两侧靠一个 has-a 引用（桥）连起来。
**触发信号**：需求同时要求「换平台/换后端」和「加 API」，且两边版本节奏不同；一套 UI over N 个平台。
**更省的替代**：一条接口 + N 个实现（只有实现侧在变）；Strategy（只有行为在变）；驱动名做成配置项交给现有库分派。只有「抽象与实现各有演化压力且要独立发布」才需要两条层级。

**最小骨架**

**Java**
```java
interface DeviceImp { void enable(); void setChannel(int c); }        // 实现侧接口
class SonyTV implements DeviceImp { public void enable() {} public void setChannel(int c) {} }
class SamsungTV implements DeviceImp { public void enable() {} public void setChannel(int c) {} }
class RemoteControl {                                                 // 抽象侧：桥就是一个 has-a 引用
    protected final DeviceImp device;
    RemoteControl(DeviceImp device) { this.device = device; }
    void buttonPressed() { device.setChannel(3); }                     // 每个方法只对着实现接口写
}
class AdvancedRemote extends RemoteControl {                           // 抽象侧独立加子类，实现侧不知道
    AdvancedRemote(DeviceImp device) { super(device); }
    void volumeUp() {}
}
class BridgeDemo {
    public static void main(String[] args) {
        RemoteControl r = new AdvancedRemote(new SonyTV());              // 换平台不动抽象侧
        r.buttonPressed();
    }
}
```
**Swift**
```swift
protocol DeviceImp { func enable(); func setChannel(_ c: Int) }   // 实现侧接口
struct SonyTV: DeviceImp { func enable() {}; func setChannel(_ c: Int) {} }
class RemoteControl {                                       // 抽象侧：桥就是一个 has-a 引用
    let device: DeviceImp
    init(_ device: DeviceImp) { self.device = device }
    func buttonPressed() { device.setChannel(3) }            // 每个方法只对着实现接口写
}
class AdvancedRemote: RemoteControl { func volumeUp() {} }   // 抽象侧独立加子类，实现侧不知道
let r = AdvancedRemote(SonyTV())
```
**TypeScript**
```ts
interface DeviceImp { enable(): void; setChannel(c: number): void }    // 实现侧
const sonyTV: DeviceImp = { enable: () => {}, setChannel: (c) => { void c } }
class RemoteControl {                                          // 抽象侧：桥 = 注入的实现引用
  constructor(protected device: DeviceImp) {}
  buttonPressed() { this.device.setChannel(3) }                // 只对着接口写
}
class AdvancedRemote extends RemoteControl { volumeUp() {} }   // 两侧各自加，互不影响
const r = new AdvancedRemote(sonyTV)
```

## Builder

**它吸收什么变化**：多步装配（buildDay、addHotel、addTickets 一类有序步骤）与每次请求不同的合法组合；客户端指挥一个抽象 builder，最后取回成品，具体 builder 负责内部表示。
**触发信号**：构造代码在攒参数、可选件、顺序规则或半构建状态，且产品本身是复合结构。
**更省的替代**：带默认值的初始化器 / struct 字面量；一步工厂；一个 `with(...) { ... }` 收集器函数返回成品。对象能一次调用造出来时，Builder 没有可吸收的变化。

**最小骨架**

**Java**
```java
class Trip {
    final String days; final int tickets;
    Trip(String days, int tickets) { this.days = days; this.tickets = tickets; }
}
interface TripBuilder { TripBuilder buildDay(); TripBuilder addTickets(int n); Trip result(); }
class CheapTripBuilder implements TripBuilder {                    // 具体 builder 管内部表示与顺序
    private final StringBuilder days = new StringBuilder(); private int tickets;
    public TripBuilder buildDay() { days.append("day"); return this; }
    public TripBuilder addTickets(int n) { tickets += n; return this; }
    public Trip result() { return new Trip(days.toString(), tickets); }   // 只有到这里才拿到成品
}
class TravelAgent {                                                 // 客户端只指挥步骤，不认识内部表示
    static Trip build(TripBuilder builder) { return builder.buildDay().addTickets(2).result(); }
}
```
**Swift**
```swift
struct Trip { var days: [String] = []; var tickets: Int = 0 }           // 复合产品
protocol TripBuilder { func buildDay(); func addTickets(_ n: Int); func result() -> Trip }
final class CheapTripBuilder: TripBuilder {          // 具体 builder 管内部表示与顺序合法性
    private var t = Trip()
    func buildDay() { t.days.append("day") }
    func addTickets(_ n: Int) { t.tickets += n }
    func result() -> Trip { t }                       // 只有到这里才拿到成品
}
func assemble(_ b: TripBuilder) -> Trip { b.buildDay(); b.addTickets(2); return b.result() }  // 客户端只指挥步骤
```
**TypeScript**
```ts
type Trip = { days: string[]; tickets: number }
class TripBuilder {                          // 攒参数 + 顺序合法性收在一处
  private t: Trip = { days: [], tickets: 0 }
  buildDay() { this.t = { ...this.t, days: [...this.t.days, 'day'] }; return this }
  addTickets(n: number) { this.t = { ...this.t, tickets: this.t.tickets + n }; return this }
  result(): Trip { return this.t }           // 半构建状态不外泄
}
const trip = new TripBuilder().buildDay().addTickets(2).result()
```

## Chain of Responsibility

**它吸收什么变化**：「哪个处理者接手这个请求」以及处理者的集合与顺序（每个 handler 持一个 successor，要么处理要么转发；发送方只认识第一个，可放兜底 handler 收尾）。
**触发信号**：多个不同对象都可能对同一个请求动作、事先不知道归谁、集合或顺序要在运行时改。
**更省的替代**：一次直接调用；按类型的 handler map / 字典分派（静态已知只有一个接手者时）；一个前置 guard。类链只有「候选集可变且顺序有意义」时才值。

**最小骨架**

**Java**
```java
abstract class Handler {                                             // 每个 handler 持一个 successor
    private Handler next;
    Handler setNext(Handler next) { this.next = next; return next; }
    boolean handle(String kind) {
        if (owns(kind)) { accept(kind); return true; }                // 接手
        return next != null && next.handle(kind);                     // 不接就往下传
    }
    protected abstract boolean owns(String kind);
    protected void accept(String kind) { System.out.println("handled " + kind); }
}
class BillingHandler extends Handler { protected boolean owns(String k) { return "billing".equals(k); } }
class NetworkHandler extends Handler { protected boolean owns(String k) { return "network".equals(k); } }
class CoRDemo {
    public static void main(String[] args) {
        Handler head = new BillingHandler();
        head.setNext(new NetworkHandler());
        boolean handled = head.handle("network");                      // 发送方只认识链头
        boolean missed = head.handle("hr");                            // 没人接手＝false：不保证被处理
        System.out.println(handled + "/" + missed);
    }
}
```
**Swift**
```swift
protocol Handler: AnyObject { var next: Handler? { get set }; func handle(_ kind: String) -> Bool }
class BaseHandler: Handler {
    var next: Handler?
    func handle(_ kind: String) -> Bool { next?.handle(kind) ?? false }   // 不接就往下传
}
class Specialist: BaseHandler { let owns: String
    init(_ owns: String) { self.owns = owns }
    override func handle(_ kind: String) -> Bool {
        kind == owns ? true : super.handle(kind)          // 接手 or 转发，二选一
    }
}
let chain = Specialist("billing"); chain.next = Specialist("network")
let handled = chain.handle("network")                     // 发送方只认识链头
assert(!chain.handle("hr"))                               // 不保证被处理——这就是 CoR 自己的代价
```
**TypeScript**
```ts
type Handler = (req: string) => boolean
const chain = (...hs: Handler[]): Handler => (req) => hs.some((h) => h(req))  // 顺序＝候选优先级；接手即停
const handle = chain((r) => r === 'billing', (r) => r === 'network')          // 每环只管自己那类
const ok = handle('billing')          // true
const missed = handle('hr')           // false：没有任何环接手——不保证被处理是 CoR 的固有代价
```

## Flyweight

**它吸收什么变化**：逻辑实例的数量。共享的内在状态只留一份无状态实例，每个「虚拟对象」的每实例状态被推到管理器持有的外部存储，并在每次操作时传入（`display(x, y, age)` 那个形状）。
**触发信号**：海量近似对象、每实例状态很小且能统一处理，并且内存/分配成本已经测出来在疼。
**更省的替代**：值类型 struct 存进数组；虚拟化列表用一个行组件渲染数据数组；interned 资源池（字体/文本 run）。没测出压力就停在低阶梯。

**最小骨架**

**Java**
```java
final class Glyph {                                                   // 内在状态：共享、不可变
    private final char ch;
    Glyph(char ch) { this.ch = ch; }
    void display(int x, int y) { System.out.println(ch + "@" + x + "," + y); }  // 外在状态每次传入
}
final class GlyphPool {                                               // 一个实例承载多种内容
    private static final java.util.Map<Character, Glyph> pool = new java.util.HashMap<>();
    static Glyph of(char c) { return pool.computeIfAbsent(c, Glyph::new); }   // 只在没见过时分配
    static int physical() { return pool.size(); }
}
class FlyweightDemo {
    public static void main(String[] args) {
        Glyph first = GlyphPool.of('A');
        Glyph reuse = GlyphPool.of('A');                                // 逻辑实例两个，物理实例一个
        first.display(0, 0); reuse.display(1, 0);
        System.out.println(GlyphPool.physical());
    }
}
```
**Swift**
```swift
struct Glyph { let char: Character }                      // 内在状态：共享、不可变
final class GlyphPool {                                  // 管理器：一份内在状态对多个逻辑实例
    private var pool: [Character: Glyph] = [:]
    func glyph(_ c: Character) -> Glyph {
        if let hit = pool[c] { return hit }
        let g = Glyph(char: c); pool[c] = g; return g     // 只在没见过时才分配
    }
}
func display(_ g: Glyph, x: Int, y: Int) { print("\(g.char)@\(x),\(y)") }  // 外在状态每次传入
let pool = GlyphPool()
display(pool.glyph("A"), x: 0, y: 0)
```
**TypeScript**
```ts
const pool = new Map<string, string>()                    // 内在状态：intern 一份
const glyph = (c: string) => { const hit = pool.get(c) ?? c; pool.set(c, hit); return hit }
const display = (g: string, x: number, y: number) => `${g}@${x},${y}`   // 外在状态每次传入
display(glyph('A'), 0, 0)
```

## Interpreter

**它吸收什么变化**：解释规则。每条语法规则一个 Expression 类，复合节点（Sequence、Repetition）递归子节点、叶子节点匹配命令，context 携带输入流与求值状态。
**触发信号**：应用内部要解析并求值一个小而稳定的语言/DSL（搜索过滤语法、配置规则、脚本）。
**更省的替代**：现成引擎或 parser generator；`indirect enum` AST + 单个 `evaluate(in:)`；parse-don't-validate 到判别式联合 + 穷尽 switch（这些非本书）。语法小且不再长大时这些就够。

**最小骨架**

**Java**
```java
class Context { String input; int pos; Context(String input) { this.input = input; } }
interface Expression { boolean interpret(Context ctx); }               // 一条语法规则一个节点
class CommandExpr implements Expression {                               // 叶子：匹配一个命令字符
    private final char word;
    CommandExpr(char word) { this.word = word; }
    public boolean interpret(Context ctx) {
        if (ctx.pos >= ctx.input.length()) return false;
        return ctx.input.charAt(ctx.pos++) == word;                     // 消费 token
    }
}
class SequenceExpr implements Expression {                             // 复合：按序递归子节点
    private final java.util.List<Expression> parts;
    SequenceExpr(Expression... parts) { this.parts = java.util.Arrays.asList(parts); }
    public boolean interpret(Context ctx) {
        for (Expression e : parts) { if (!e.interpret(ctx)) return false; }
        return true;
    }
}
class RepetitionExpr implements Expression {                            // 复合：子节点吃到不匹配为止
    private final Expression part;
    RepetitionExpr(Expression part) { this.part = part; }
    public boolean interpret(Context ctx) { while (part.interpret(ctx)) { System.out.println("eat"); } return true; }
}
```
**Swift**
```swift
final class Context { let input: [String]; var pos = 0; init(_ i: [String]) { input = i } }
protocol Expression { func interpret(_ ctx: Context) -> Bool }        // 一条语法规则一个节点
struct CommandExpr: Expression { let word: String
    func interpret(_ ctx: Context) -> Bool {
        defer { ctx.pos += 1 }
        return ctx.pos < ctx.input.count && ctx.input[ctx.pos] == word   // 叶子：匹配一个命令
    }
}
struct SequenceExpr: Expression { let parts: [Expression]
    func interpret(_ ctx: Context) -> Bool { parts.allSatisfy { $0.interpret(ctx) } }  // 复合：递归子节点
}
let program = SequenceExpr(parts: [CommandExpr(word: "up"), CommandExpr(word: "down")])
```
**TypeScript**
```ts
type Ctx = { input: string[]; pos: number }
type Expr = (c: Ctx) => boolean                            // 规则少时，一个函数就是一个节点
const cmd = (w: string): Expr => (c) => { const hit = c.input[c.pos] === w; c.pos += 1; return hit }
const seq = (...es: Expr[]): Expr => (c) => es.every((e) => e(c))     // 复合节点递归子节点
const program = seq(cmd('up'), cmd('down'))
program({ input: ['up', 'down'], pos: 0 })
```

## Mediator

**它吸收什么变化**：对象之间协调与规则的所有权。同事不再互相引用，只向协调者报告状态变化并响应它的请求，把 N×N 的消息网收成星形。
**触发信号**：一组对象各自认识并直连许多其他对象；加一个参与者要改许多别处；规则所有权散在各处。
**更省的替代**：保留直接引用（只有一两个简单关系时）；一个回调/闭包；一张路由表。只是共享一份状态时，一个 observable store 比新建 mediator 类便宜。

**最小骨架**

**Java**
```java
abstract class ChatMediator {                                          // 协调者持有这张网
    final java.util.List<Member> members = new java.util.ArrayList<>();
    void join(Member m) { members.add(m); }
    abstract void post(String msg, Member from);                        // 路由规则只在这一处
}
class Member {                                                          // 同事：不再互相引用
    final String name; private final ChatMediator mediator;
    Member(String name, ChatMediator mediator) { this.name = name; this.mediator = mediator; mediator.join(this); }
    void send(String msg) { mediator.post(msg, this); }                  // 只报告变化，不点名对象
}
class Room extends ChatMediator {
    public void post(String msg, Member from) {
        for (Member m : members) { if (m != from) System.out.println(m.name + ": " + msg); }
    }
}
class MediatorDemo {
    public static void main(String[] args) {
        ChatMediator room = new Room();
        Member alice = new Member("alice", room);
        Member bob = new Member("bob", room);
        alice.send("hi");                                                // 加参与者只改注册，不动别的成员
        bob.send("yo");
    }
}
```
**Swift**
```swift
protocol ChatMediator: AnyObject { func post(_ msg: String, from m: Member) }   // 规则收口处
class Member {                                            // 同事：不再互相引用
    let name: String
    weak var mediator: ChatMediator?
    init(_ name: String) { self.name = name }
    func send(_ msg: String) { mediator?.post(msg, from: self) }   // 只报告变化，不点名对象
}
final class Room: ChatMediator {                          // 具体中介者持有这张网
    var members: [Member] = []
    func post(_ msg: String, from m: Member) {
        for other in members where other !== m { print("\(other.name): \(msg)") }  // 路由规则只在这
    }
}
```
**TypeScript**
```ts
type Member = { name: string; send(msg: string): void }
class Room {                                              // 星形：同事只连中心，不再互指
  constructor(private members: Member[]) {}
  broadcast(from: Member, msg: string) {
    for (const m of this.members) if (m !== from) m.send(`${from.name}: ${msg}`)  // 规则只在这一处
  }
}
const a: Member = { name: 'a', send: (m) => console.log(m) }
const b: Member = { name: 'b', send: (m) => console.log(m) }
const room = new Room([a, b])
```

## Memento

**它吸收什么变化**：originator 的内部状态要能存一份并回到过去，同时对外保持不透明——客户端只负责保管快照并交还。
**触发信号**：undo、回到检查点、存档进度，且内部状态复杂到不能让外部改。
**更省的替代**：直接序列化（附录自己就建议考虑 Serialization）；状态本来就是值对象时直接复制；`Codable` 快照 / `NSUndoManager` / `structuredClone` / `useReducer` 历史栈（非本书）。

**最小骨架**

**Java**
```java
final class Editor {                                                   // originator
    private final java.util.List<String> lines = new java.util.ArrayList<>();   // 对外不透明
    void type(String s) { lines.add(s); }
    Memento snapshot() { return new Memento(new java.util.ArrayList<>(lines)); }  // 交出只读快照
    void restore(Memento m) { lines.clear(); lines.addAll(m.state()); }           // 只认自家快照
}
final class Memento {                                                   // 客户端只能保管与交还
    private final java.util.List<String> state;
    Memento(java.util.List<String> state) { this.state = java.util.Collections.unmodifiableList(state); }
    java.util.List<String> state() { return state; }                     // 包内可见，不对 client 打开
}
final class UndoStack {                                                  // caretaker：不理解内容
    private final java.util.Deque<Memento> history = new java.util.ArrayDeque<>();
    void push(Memento m) { history.push(m); }
    Memento pop() {
        if (history.isEmpty()) throw new java.util.NoSuchElementException("no snapshot");
        return history.pop();                                            // LIFO：栈顶才是最近一次
    }
}
```
**Swift**
```swift
struct EditorState { let lines: [String] }                 // memento：对外不透明
final class Editor {                                       // originator
    private var lines: [String] = []
    func type(_ s: String) { lines.append(s) }
    func snapshot() -> EditorState { EditorState(lines: lines) }   // 交出只读快照
    func restore(_ m: EditorState) { lines = m.lines }             // 只认自家快照
}
final class UndoStack {                                    // caretaker：只保管，不解读内容
    private var history: [EditorState] = []
    func push(_ m: EditorState) { history.append(m) }
    func pop() -> EditorState? {                        // LIFO：栈顶才是最近一次
        guard let last = history.last else { return nil }
        history.removeLast(); return last }
}
```
**TypeScript**
```ts
class Editor {                                  // originator：内部状态对外不透明
  private lines: string[] = []
  type(s: string) { this.lines.push(s) }
  snapshot() { return { lines: [...this.lines] } }         // memento：只读拷贝
  restore(m: { readonly lines: readonly string[] }) { this.lines = [...m.lines] }
}
const undoStack: { readonly lines: readonly string[] }[] = []  // caretaker：只排队，不解读
const editor = new Editor()
editor.type('a'); undoStack.push(editor.snapshot())
editor.restore(undoStack.pop()!)
```

## Prototype

**它吸收什么变化**：造哪个具体类，以及创建成本。客户端向注册表要实例并拿到样板的副本，类型选择与初始化细节都被藏在克隆里。
**触发信号**：实例化昂贵或繁琐（构造器塞满状态细节），或具体类型必须在运行时从一份可配置集合里挑。
**更省的替代**：工厂 + 配置表（类型能由参数决定时，附录自己说「有简单构造器就用工厂」）；Swift struct 赋值后改字段（语言白送拷贝）；TS `{ ...template }` / `structuredClone` 配注册表（非本书）。

**最小骨架**

**Java**
```java
abstract class Monster {
    protected final String kind; protected int hp;
    Monster(String kind, int hp) { this.kind = kind; this.hp = hp; }
    abstract Monster prototype();                       // 造哪个具体类，由被克隆的对象自己决定
    String describe() { return kind + "/" + hp; }
}
final class Orc extends Monster {
    private int rage;
    Orc(String kind, int hp, int rage) { super(kind, hp); this.rage = rage; }
    private Orc(Orc src) { super(src.kind, src.hp); this.rage = src.rage; }   // 深浅拷贝在这里决定
    Monster prototype() { return new Orc(this); }                              // 不 new、不 switch 类型
}
final class PrototypeRegistry {
    private static final java.util.Map<String, Monster> samples = new java.util.HashMap<>();
    static { samples.put("orc", new Orc("orc", 10, 0)); }              // 样板集可运行时配置
    static Monster spawn(String key) { return samples.get(key).prototype(); }
}
```
**Swift**
```swift
class Monster {
    let kind: String; var hp: Int
    init(kind: String, hp: Int) { self.kind = kind; self.hp = hp }
    func clone() -> Monster { Monster(kind: kind, hp: hp) }   // 子类必须重写，否则克隆降级成父类
}
class Boss: Monster { override func clone() -> Monster { Boss(kind: kind, hp: hp) } }
enum Registry {                                             // 运行时从可配置样板集里挑
    static var samples: [String: Monster] = ["boss": Boss(kind: "boss", hp: 99)]
    static func spawn(_ key: String) -> Monster { samples[key]!.clone() }   // 不 new，复制样板
}
```
**TypeScript**
```ts
type Unit = { kind: string; hp: number }
const boss: Unit & { clone(): Unit } = { kind: 'boss', hp: 99, clone() { return { ...this } } }  // spread 即克隆
const samples: Record<string, { clone(): Unit }> = { boss }      // 样板集可运行时配置
const spawn = (k: string): Unit => samples[k]!.clone()           // 不 new，也不 switch 类型
```

## Visitor

**它吸收什么变化**：「要对这棵结构做什么操作」。操作被推到结构之外：遍历器走每个节点，visitor 通过 `getState()` 式的面收集节点状态，新能力只加 visitor 类。
**触发信号**：在一棵稳定对象结构上反复加新操作（报表、导出、分析），且不想每次改动每个节点类。
**更省的替代**：判别式联合 + 穷尽 switch / handler map、`indirect enum` + switch（非本书）——多数现代语言里这就替掉了双派发；只有单个操作时让方法住在节点上。

**最小骨架**

**Java**
```java
interface Node { void accept(NodeVisitor v); }                          // 结构稳定
interface NodeVisitor { void visit(Leaf leaf); void visit(Group group); }  // 做什么操作住在结构之外
final class Leaf implements Node {
    private final String name; Leaf(String name) { this.name = name; }
    String name() { return name; }
    public void accept(NodeVisitor v) { v.visit(this); }                 // 双派发第二跳
}
final class Group implements Node {
    private final String name; private final java.util.List<Node> children;
    Group(String name, Node... children) { this.name = name; this.children = java.util.Arrays.asList(children); }
    String name() { return name; }
    java.util.List<Node> children() { return children; }
    public void accept(NodeVisitor v) { v.visit(this); }
}
final class PrintNames implements NodeVisitor {                          // 加操作＝加 visitor，节点类不动
    public void visit(Leaf leaf) { System.out.println(leaf.name()); }
    public void visit(Group group) {
        System.out.println("[" + group.name() + "]");
        for (Node n : group.children()) n.accept(this);
    }
}
final class CountLeaves implements NodeVisitor {                          // 换 visitor 不必重编译结构
    int total;
    public void visit(Leaf leaf) { total++; }
    public void visit(Group group) { for (Node n : group.children()) n.accept(this); }
}
```
**Swift**
```swift
indirect enum ASTNode { case leaf(String); case group([ASTNode]) }      // 结构稳定
protocol ASTNodeVisitor { func visit(_ name: String) -> String; func visit(_ children: [ASTNode]) -> String }
struct CountVisitor: ASTNodeVisitor {                                // 新操作＝新 visitor，节点类不动
    func visit(_ name: String) -> String { "1" }
    func visit(_ children: [ASTNode]) -> String { children.map { accept($0) }.joined(separator: "+") }
    func accept(_ n: ASTNode) -> String {
        switch n { case .leaf(let s): return visit(s); case .group(let c): return visit(c) }
    }
}
```
**TypeScript**
```ts
type ASTNode = { kind: 'leaf'; name: string } | { kind: 'group'; children: ASTNode[] }
type Visitor = { leaf(n: { name: string }): string
                 group(children: ASTNode[], rec: (n: ASTNode) => string): string }
const render = (v: Visitor) => (n: ASTNode): string =>               // 双派发：结构只走一遍
  n.kind === 'leaf' ? v.leaf(n) : v.group(n.children, render(v))
const count: Visitor = { leaf: () => '1', group: (c, rec) => c.map(rec).join('+') }        // 加操作＝加 visitor
const names: Visitor = { leaf: (n) => n.name, group: (c, rec) => c.map(rec).join(' ') }
```

## 别上的情形

- 能停在更低阶梯就别上：一次调用造得出（Builder）、状态本是值对象（Memento）、只有一个静态已知的接手者（CoR/Mediator）、单边在变（Bridge）、没测出内存压力（Flyweight）
- 语法会长大或要优化 → 别手写 Interpreter；封装重要 → 别用 Visitor（附录写得直接）
- **本文件是目录级，故意浅**：附录没给任何一模式的实现细节、失效模式、并发语义或与框架的边界；这里每条判据只能用来**缩小候选集**。任何一次选择若要影响模块划分、数据模型或跨团队契约，必须先回到专门来源（该模式原始出处 + 目标框架官方实现）再核一遍（非本书的自律条款）

## 更省的替代

九模式共同的阶梯（逐级确认上一级不够再升级）：

1. 数据/配置：注册表 `Map<string, Template>`（Prototype）、handler map 按类型分派（代 CoR/Mediator 的路由）、共享样式/字体 intern 表（代 Flyweight）、驱动名写进配置（代 Bridge 的一侧）
2. 闭包/函数参数：带默认值的初始化器或 struct 字面量（代 Builder）；`[handler1, handler2]` 数组顺序应用（代 CoR 类结构）；`(state) -> Snapshot` 闭包（代 Memento 类型）
3. 单个注入对象：一个 builder/收集器、一个 coordinator/observable store（Mediator）、一个 TreeManager 式状态持有者（Flyweight）、一个 registry + clone 函数（Prototype）
4. 才轮到模式类结构：Builder 在「客户端必须掌控步骤顺序且产物是复合结构」时降不下来；Visitor 在「新操作增长远快于节点类型」时降不下来；Bridge 在「两侧各有版本节奏且要独立发布」时降不下来。其余（Interpreter/Memento/Prototype/Flyweight）在现代语言里几乎都能停在第 1-3 级

## 共同形状

九块骨架其实是同一句：把某种「知识」从使用它的地方搬到一个单独的类型里。下表是九行全的口径；每个模式自己的可编译骨架在它自己的小节里。

```text
client ──▶ seam(抽象) ──▶ 承载该知识的参与者 ──▶ 被操作的对象/结构
   Builder    步骤顺序        具体 builder             复合产品
   Bridge     两侧各自演化    实现接口 + N 实现         抽象侧子类
   CoR        谁接手          handler + successor       请求
   Flyweight  实例数量        池/管理器 + 外部状态       逻辑实例
   Interpreter 求值规则       表达式节点（复合/叶子）    token 流 + context
   Mediator   谁跟谁协调      协调者持有同事            同事之间的消息
   Memento    历史            不透明快照                originator
   Prototype  造哪个具体类    样板 + clone              新实例
   Visitor    做什么操作      visitor.accept            节点结构
```
## 上了之后要盯的代价

- Bridge：双份类层级 + 每次调用多一层间接；层级立起后任何单边改动也要穿过桥改两边
- Builder：客户端要比一步工厂懂更多领域知识（步骤与顺序），多一个类型和「取回之前」的中间状态
- CoR：不保证被处理（请求可一路落到链尾），运行时行为难观测难调试，每个 handler 多一次跳转
- Flyweight：个体逻辑实例再也不能各自行为；状态中心化是很大的耦合风险；过早共享挡住未来的 per-object 字段
- Interpreter：一规则一类，语法一长就失控；树遍历本身慢
- Mediator：设计不谨慎时长成装着全部规则的神级对象（书写得很明白）；每次交互多一跳，且它成为改动最频繁的类
- Memento：存取可能费时、吃内存；多一个不透明类型和「谁保管快照」这条所有权线
- Prototype：深浅拷贝容易搞错；没有真拷贝语义的语言里 clone 的来源很隐晦
- Visitor：节点封装被打破（要靠 getState() 面摊开内部），改结构本身变难
- 通用账：每个都是额外的类型 + 一次间接 + 一个调试落点；目录级条目的真实成本常常是「以为它和那半页一样简单」

## 形近模式判别

- Bridge vs Adapter vs Decorator：按**变化压力**分类——新平台 + 演化中的 API（Bridge，提前设计、两条层级）、接口错了（Adapter，事后修）、功能一层层加（Decorator，保住接口）。因为图示相似就立两条层级，等于把一次性包装变成永久重复
- CoR vs Mediator vs Observer：按**通信形状**分类——单请求多候选 / 多方一协调者 / 一事件多接收方
- Flyweight vs Prototype vs Memento：压力分别落在实例数量 / 实例创建 / 实例历史上，且前两者方向相反（共享干掉身份，克隆假设身份），同一类型只选一个
- Builder vs 工厂族：一步造出已知产物归工厂；多步、客户端掌控装配顺序、产物是复合结构归 Builder
- Memento vs 序列化：除「存一份」外是否还必须让外人看不见内部？否就直接复制；Visitor vs Composite/Iterator：操作住节点里（Composite）、只遍历不加工（Iterator）、新操作远快于新节点类型地增长（Visitor）

## 组合与框架替身

框架替身（全部非本书，别手写机器）：CoR → Express/Koa middleware、servlet filter、axios/fetch interceptor、UIKit responder chain；Mediator → Redux/Zustand store、SwiftUI coordinator、XState actors、消息 broker；Flyweight → 虚拟化列表、interned 字符串、共享 theme/style、ECS archetype 存储；Memento → `Codable` 快照、值类型复制、`structuredClone`、`useReducer` 历史栈、NSUndoManager；Builder → fluent query builder、Lombok `@Builder`、测试数据工厂；Prototype → Swift struct 赋值即拷贝、对象 spread、`NSCopying`；Bridge → JDBC/ODBC 驱动分离、跨平台窗口工具包、六边形架构的 port/adapter；Interpreter → ANTLR/tree-sitter、schema/validator 运行时、查询规划器；Visitor → 编译器 AST visitor、判别式联合 + 穷尽 switch/handler map。
可叠的组合：Builder + Flyweight、Mediator + CoR、Bridge + Abstract Factory（抽象侧工厂发实现侧对象）——附录没验证过这些搭配，当作待验证假设（非本书）

## 决策问句

1. 我能不能用一句话说出这一模式这次要吸收的**那个**变化？说不出就退回第 12 章的 pattern-first 禁令。
2. 阶梯第 1-3 级（数据 / 闭包 / 单个注入对象）试过了吗？平台是否已有替身（middleware、store、Codable、interning）？
3. 变化压力属于哪一类：数量、创建、历史、接手者、协调规则、操作、装配步骤、还是两边各自演化？——这直接决定九选一。
4. 这个判断要落进架构吗？若是，我去哪个专门来源复核过，复核结论和这里一致吗？

## 证据

- 源文件：《Head First Design Patterns》1st ed.（Eric Freeman & Elisabeth Freeman, with Kathy Sierra & Bert Bates；O'Reilly, 2004）电子版，附录（第 14 章位）书页 pp.611-629；正文侧只另引三处：p.588（模式与意图配对练习，含 Adapter/Decorator）、pp.590-591（类别表，九模式在表内位置）、pp.606-607（反模式卡）。换算：正文 PDF 页 = 书页 + 38。
- 逐模式书页：总起 p.611；Bridge pp.612-613；Builder pp.614-615（与工厂的对比在 p.615）；CoR pp.616-617；Flyweight pp.618-619；Interpreter pp.620-621；Mediator pp.622-623；Memento pp.624-625（含「考虑用 Serialization」）；Prototype pp.626-627；Visitor pp.628-629（含「封装重要时别用」）
- 书中明说的代价（逐条对应上一节）：Bridge 双层级与间接、Builder 要求客户端懂更多、CoR 不保证被处理且难调试、Flyweight 内在/外在状态与过早共享风险、Interpreter 语法变大改用 generator、Mediator 会长成神对象、Memento 费时费内存、Prototype 深浅拷贝、Visitor 破封装
- **本书没有 Bridge vs Adapter vs Decorator 的对照判别**：全文（不区分大小写）Bridge 只落在书页 pp.590-591（类别表）、pp.612-613（附录条目本身）、pp.631-632（索引），三处都没有把它和 Adapter/Decorator 放在一起比。本文件里那组决定性问题属下面这条的写作约束，不要当书中原话引用。
- 非附录来源与（非本书）：九模式全部现代映射（JDBC、六边形、ECS、ANTLR、XState、NSUndoManager、Lombok、Codable、structuredClone）、Bridge/Adapter/Decorator 判别、CoR/Mediator/Observer 形状判别、数量-创建-历史判别、本文件顶层变化轴分组、「目录深度须回专门来源复核」条款、最小骨架共同形状与组合搭配假设——均为写作约束而非书中原话
