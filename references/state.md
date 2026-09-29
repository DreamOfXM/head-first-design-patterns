# State（中文：状态，第 10 章）

## 它吸收什么变化
变化轴是"同一批动作，在不同状态下哪些合法、做完去哪"；不变的是动作集合和 Context 手里的数据。
State 把按状态字段分支的行为搬进"每个状态一个类型"，于是当前状态自己答题，每条转移只写在一处。
另一半被搬走的是转移知识：不再散落在各个动作方法的开头，而是跟着能观察到它的那个状态住。

## 触发信号
- 三个以上方法开头都在重测同一个 status 字段 → 这个值是一座隐形的类
- 进入某状态在 A 方法里赋值、离开在 B 方法里赋值 → 转移没有单点归属
- 加一个新状态要在每个动作方法里补一条分支 → OCP 正在被这批条件式破坏
- 需求里画得出状态图（圆圈＋带标号的箭头）→ 角色可以一比一对上
- 分支里开始交叉读第二个状态轴（库存、促销开关）→ bug 集中在没人碰的旧分支
- 只有一个方法按 status 分支、状态差别就是一行日志、规范里没有状态图 → 反指信号，别上

## 别上的情形
- 2 个状态 × 1-2 个动作且看着稳定：不上——一个 switch／reduce 就够；上了——几个只回同一句拒绝的类（阈值是判据不是事实，非本书）。
- 画不出离散状态与合法转移（其实是调用方选的偏好／模式）：不上——那属于 Strategy 或 props/配置；上了——多一个 manager 对象和藏起来的转移码，味道一点没减。
- 一次性脚本、三两周就扔的代码：不上——留条件式；上了——类的税照付，收益兑现不了。
- 状态类为了做事要往 Context 上再开一堆 getter：不上——先质疑接口；上了——公开 API 被内部状态撑宽。
- 客户端在调 setState：这不是"要不要用 State"的问题，是已经上坏了——状态属主只能有一个。

## 更省的替代
1. 数据／配置：转移表——行 `[from, event] -> (guard, actions, to)` ＋ 一个 reduce 函数；非法转移直接不可表示，整张图可枚举可测（非本书）。
   够：状态之间只差"下一步去哪"。不够：某状态的行为本身大量分支或带 IO——表退化成一套没有类型检查的私有语言。
2. 闭包／函数参数：一个纯函数 `reduce(state, event) -> state`，状态是**值**不是类（Swift enum + associated values；TS discriminated union）（非本书）。
   够：状态少、动作少、演进慢，且转移能从数据算出来。不够：不同团队各自扩状态、要把每个状态的合法响应局部化成一块独立代码。
3. 单个注入对象：把行为对象注入进 Context——但先问是谁在换它：调用方配置着换，那是 Strategy，不是 State。
   够：行为由外部挑选、彼此可互换、没有合法转移约束。不够：必须由对象内部事件沿合法边推进。
4. 才轮到 State：每状态封装自己那一坨合法响应，且**转移目标依赖运行时数据**（要看实时库存、要等异步结果）——这时表和价值类型枚举都得把行为放回节点上。

## 最小骨架
**伪代码（角色与方向）**
```
Context(GumballMachine)：持有 state 引用 + 数据(count)；每个动作转发给当前状态
    insertQuarter() -> state.insertQuarter(self)     # 客户端只碰 Context
    setState(_:)                                    # 模块内可见，绝不 export
State 接口：一个 Context 动作对应一个 handler（动作集固定，才换得起状态）
HasQuarterState.insertQuarter()：显式拒绝，不是空体
SoldState.dispense()：读 count → 选下一个状态；兄弟从 Context 的 getter 取，不自己 new
转移 = (事件, 守卫, 数据) -> 下一个状态
初始状态由数据算出（count>0 → NoQuarter，否则 SoldOut），不另存一份真相
调用方向：Client -> Context -> 当前 State -> Context.setState
变化点：每个状态里合法的响应与去向｜不变点：动作集合与 Context 数据
```
**Java**
```java
interface State { void insertQuarter(); void turnCrank(); }          // 动作集固定，才换得起状态
class GumballMachine {
    private final java.util.Map<String, State> states = new java.util.HashMap<>();
    private State state;                                              // 不 export＝状态只有一个属主
    private final int count;
    GumballMachine(int count) {
        this.count = count;
        states.put("soldOut", new SoldOutState(this)); states.put("noQuarter", new NoQuarterState(this));
        states.put("hasQuarter", new HasQuarterState(this)); states.put("sold", new SoldState(this));
        state = states.get(count > 0 ? "noQuarter" : "soldOut");       // 初始状态由数据算出，不另存真相
    }
    void setState(String key) { state = states.get(key); }             // 转移经 context，兄弟不自己 new
    int count() { return count; }
    void insertQuarter() { state.insertQuarter(); }                     // 客户端只碰 Context
    void turnCrank() { state.turnCrank(); }
    void reject(String why) { System.out.println("拒绝：" + why); }
    boolean canWin() { return count > 1 && java.util.concurrent.ThreadLocalRandom.current().nextBoolean(); }
}
class NoQuarterState implements State {
    private final GumballMachine m; NoQuarterState(GumballMachine m) { this.m = m; }
    public void insertQuarter() { m.setState("hasQuarter"); }
    public void turnCrank() { m.reject("还没投币"); }
}
class HasQuarterState implements State {
    private final GumballMachine m; HasQuarterState(GumballMachine m) { this.m = m; }
    public void insertQuarter() { m.reject("已经投过一枚"); }            // 非法事件：明确拒绝，不空体、不抛
    public void turnCrank() { m.setState(m.canWin() ? "winner" : "sold"); }   // 转移带守卫、带运行时数据
}
class SoldState implements State {
    private final GumballMachine m; SoldState(GumballMachine m) { this.m = m; }
    public void insertQuarter() { m.reject("正在出货"); }
    public void turnCrank() { m.reject("正在出货"); }
}
class SoldOutState implements State {
    private final GumballMachine m; SoldOutState(GumballMachine m) { this.m = m; }
    public void insertQuarter() { m.reject("已售罄"); }
    public void turnCrank() { m.reject("已售罄"); }
}
```
**Swift**
```swift
// ↓↓↓ 配套，不是模式内容
struct Machine {
    var count = 0
    private(set) var phase: Phase = .noQuarter
    mutating func reject(_ why: String) { print("拒绝：\(why)") }
    mutating func setState(_ p: Phase) { phase = p }
    mutating func rollIsWinner() -> Bool { count > 0 && Bool.random() }
}

enum Phase { case noQuarter, hasQuarter, sold, soldOut, winner }   // 状态当值：多数项目到这就够（非本书）
protocol MachineState {                     // 才轮到 State：每个状态封装自己合法的响应
    func insertQuarter(_ m: inout Machine) // context 每次调用传入、不存字段 → 无字段状态可共享
    func turnCrank(_ m: inout Machine)
}
struct SoldOutState: MachineState {
    func insertQuarter(_ m: inout Machine) { m.reject("已售罄") }   // 非法事件：明确拒绝，不空体、不抛
    func turnCrank(_ m: inout Machine) { m.reject("已售罄") }
}
struct SoldState: MachineState {
    func insertQuarter(_ m: inout Machine) { m.reject("正在出货") }
    func turnCrank(_ m: inout Machine) {   // 转移带守卫、带运行时数据，经 context 取兄弟
        m.setState(m.count > 1 && m.rollIsWinner() ? .winner : (m.count > 0 ? .sold : .soldOut))
    }
}
```
**TypeScript**
```ts
// ↓↓↓ 配套，不是模式内容
type GumballState = { insertQuarter(m: Machine): void; turnCrank(m: Machine): void }
const winnerState: GumballState = { insertQuarter() {}, turnCrank() {} }
const soldState: GumballState = { insertQuarter() {}, turnCrank() {} }

type S = { tag: "noQuarter" } | { tag: "hasQuarter" } | { tag: "sold" };   // 判别联合 + 一个 reducer（非本书）
type E = { type: "QUARTER" } | { type: "CRANK" };
function reduce(s: S, e: E, d: { count: number }): S {   // 转移单点
  if (s.tag === "noQuarter" && e.type === "QUARTER") return { tag: "hasQuarter" };
  if (s.tag === "hasQuarter" && e.type === "CRANK") return { tag: "sold" };
  return s;                                               // 非法组合：不新增分支，也就无处写错
}
class Machine {
  private state?: GumballState
  setState(s: GumballState) { this.state = s }            // 不 export＝状态只有一个属主
  reject(_why: string) {}
  canWin() { return false }
}
class HasQuarterState implements GumballState {           // 才轮到 State：行为按状态局部化
  insertQuarter(m: Machine) { m.reject("已经投过一枚") }
  turnCrank(m: Machine) { m.setState(m.canWin() ? winnerState : soldState); }  // 兄弟经 getter，不 new
}
```
三语分工：Java 段是本书语言的骨架（原书示例是 Java／GumballMachine）；Swift／TS 段是现代语言映射（非本书）。

## 上了之后要盯的代价
- 类的数量就是灵活性的价格；对手是没人再敢维护的巨型条件式。要藏的是**暴露给客户端**的类数：具体状态模块内不导出，别把它们做成扩展点。
- 加状态便宜（一个类＋几条指向它的转移），加动作贵：State 接口上多一个方法，每个已有状态都得实现。别声称在动作方向也开放封闭；让新动作活得下去的是带默认体的抽象基类，光一个接口做不到。
- 状态持有 Context 换来转移能力，也换来双向依赖：单测一条转移要拉起整机，状态里还会顺手用不相关的 Context 副作用。更省的形状是把 Context 每次调用传入，或让状态只返回（下一个状态＋副作用）（非本书）。
- 别为服务状态而撑宽 Context 的公开 API。
- 共享状态（每个 Context 复用同一个静态实例）的前提是状态**不带自己的数据**；状态里一旦有计数器／随机源就变成每 Context 一个实例。把会变的字段共享出去，等于把一个 Context 的历史漏进另一个（非本书）。
- 公开 setState 是缺陷：客户端背着守卫改状态，所有守卫当场失效；测试和后台任务也不能绕过同一个转移函数直接写 status。
- Context 里无条件串调两个状态方法（先 turnCrank 再 dispense）会让每个状态再守一遍——让第一步把成功与否显式化，或由状态自己决定后续；但也别把次序藏进状态里，图上就看不见了。
- 不许留静默空体（调用方拿不到任何信号），也不许为"用户常见误操作"抛异常；同一形状还得保持——按状态缩接口就丢掉多态。
- 转移由状态做还是由 Context 做：图固定 → 放 Context；目标取决于实时数据 → 放观察到它的那个状态。全收回 Context 就是把条件中枢请回来。
- 初始状态与补货都是**从数据算出来的**：构造时按 count 选状态，refill 要同时写数据和状态；把状态对象的身份（类名／序号）当唯一真相存下来，数据和状态迟早打架——恢复时按持久化数据重算状态（非本书）。
- 两个近亲状态想并成一个类＋一个布尔位：判据是那个标志有没有独立的改变理由（促销起止）——有就别并，并了一个类两个理由；若痛点只是重复的拒绝文案，用共享抽象基类去重，别用标志位。

## 形近模式判别
- vs Strategy（同一张类图，不同意图）：谁在换它——外部配置／调用方随意换 → Strategy；对象内部事件沿合法转移换 → State。第二问：存不存在"合法转移"这条约束。
- vs 枚举＋switch：下一个要加的是状态还是动作？状态数、动作数和演进速度说了算，阈值是判据不是事实（非本书）。
- vs 转移表＋一个 reduce：各状态是否只差去向？只差去向 → 表；每个状态有自己的行为重活 → 类。
- vs 字段＋布尔位：这个标志有独立的改变理由吗？有 → 它是第二个状态轴，别并进一个类。

## 组合与框架替身
- 与 Context 的边界：动作全部经由 Context 到达状态，客户端只发请求、不直接持有状态对象。
- 与抽象基类：多个状态重复同样的拒绝文案时，用带默认体的基类；但转移选择绝不放进基类——那是条件中枢换皮回来了。
- 现代替身（非本书）：XState 的 createMachine（states 的 key＝具体状态，on 映射＝handler，interpreter＝Context）＋ useMachine/useInterpret；Swift 的 enum + associated values 配一个 reduce（每个 feature reducer 只拥有那个 enum，不再另存 status 字段）；后端：行上的 status 列 + 唯一写者 transition(row, event)。
- 并发写状态（非本书）：转移表带 guard 时，落库要用 `WHERE status = ...` 的比较交换，别让过期守卫被第二个 worker 满足。
- 反指信号：组件里 dispatch 一个 SET_STATE 随意换状态——那说明你想要的其实是 Strategy。

## 决策问句
1. 画得出离散状态和带标号的合法转移吗？画不出，State 只会加一个 manager 对象和看不见的转移码。
2. 谁在换这个对象：调用方的配置，还是对象内部处理的事件？
3. 现在几个状态、几个动作，以后哪个方向会长？低于某个规模就留着 switch（阈值是判据，非本书）。
4. 每一条转移是不是只写在一个地方？写两处就一定有守卫漏在一处。
5. 状态类自带字段吗？没有才谈共享实例；有就每 Context 一个，并接受对象数量上升。

## 证据
源文件：《Head First Design Patterns》1st ed.（Eric Freeman & Elisabeth Freeman, with Kathy Sierra & Bert Bates；O'Reilly, 2004）电子版，第 10 章，书页 pp.385-428（本文件引用的页区间 p.388-428）。换算：正文 PDF 页 = 书页 + 38。
引用点：p.396 与 p.425（状态条件式的味道、OCP 与埋起来的转移）、p.398/p.407（新设计步骤与收益）、p.401-405（状态持有 Context、setState、无条件串调）、p.410（定义与类图）、p.411（同图不同意图）、p.412（转移归属、可共享的无字段状态、类数量与包内可见、抽象基类加方法、动态转移）、p.413-417（WinnerState、守卫与随机数、售罄态的整排拒绝、布尔位合并之争）、p.418-420（fireside 与匹配练习）、p.426（行为矩阵）、p.428（refill 同时写数据与状态）。
标了（非本书）的条目：可共享状态漏历史的说法、状态持有 Context 的可测性与"返回（下一状态＋副作用）"补救、加动作的对称代价、持久化时重算状态、转移表作为一等选项、枚举＋switch 优于模式的数值阈值（以上对应 distill 中 INFERRED: yes 的行）；最小骨架的 Swift／TS 段、"现代替身"与并发落库段（原书只有 Java／GumballMachine）。
