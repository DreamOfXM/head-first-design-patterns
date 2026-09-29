# Command（中文：命令，第 6 章）

## 它吸收什么变化
- 变化轴有两条，同时变：**谁触发**（按钮 / endpoint / 定时任务 / UI 事件）与**做什么**（哪个 vendor 类、哪段工作）。把它们直接内联进触发类，任何一个变化都要改触发类。
- 不变的部分：触发器只管"按一下"—— 存一个命令、调它的 `execute()`。
- 搬走的是"把工作知道在哪里"：`Invoker` 存命令值、`Client` 构造具体命令并绑好 `Receiver`，Invoker 与 Receiver 互相不引用（p.229 / p.234 / p.245）。

## 触发信号
- 触发类里出现 `if slot is Light … else if Hottub …` 的类型测试链，每来一个新厂商类都要在最常用的文件里加分支并重测 → 把分支换成"存一个命令"，不是把分支排得更整齐（p.233）。
- 一个类同时干三件事：构造工作对象、决定何时触发、执行工作本身 → 四角色该分开了。
- 槽位/按键/endpoint 绑什么动作由配置、数据库行或用户设置决定，且集成会持续新增 → 参数化 invoker（七个 on/off 槽位数组，p.244 / p.248）。
- invoker 代码开始长出 `if (cmd != null)` 或每个调用点都有可选链 → 默认槽位放 NoCommand，不放 null（p.252）。
- 需求出现"撤销 / 回退上一次改动 / 取消这次操作" → 命令加 `undo()`，invoker 存历史（p.254-256）。
- Receiver 暴露的是 set-level API（high/medium/low、setVolume、move）而不是对称 on/off，而 undo 必须回到**改动前那一档** → 需要在改之前抓状态（p.258-259）。
- "一键派对 / 一键部署 / 批量审批" = 若干已有动作当一个单元跑 → 宏命令（组合出来的列表，p.262-264）。
- 要把活儿排队给固定 N 个线程，或要落日志、崩溃后按序重放、把一批操作当一个事务 → 因为计算是一个**值**，才能入队与序列化（p.266-267）。

## 别上的情形
- 一个固定调用方调一个固定方法：直接调用。不上会怎样：少一层；上了付什么账：接口 + 注册表 + 一个只为包住函数调用而存在的类层次。本章的要点是**条件式**的（p.268）。
- 只需要"稍后再跑"：闭包属性足够，不要协议不要 registry。
- 加 `undo()` / `store()` / history 到没人能请求撤销的操作：状态快照是真金白银的内存账。
- 命令自己把活全干完（smart command）却指望它"更解耦"：invoker 照样解耦，但你丢了换个 receiver 重放同一逻辑的能力，也丢了按 receiver 参数化（p.265 FAQ；本章也说 smart command 并不罕见，p.268）。
- 用命令对象来"给每个动作一个类"而没有可变触发：类数量涨了，耦合没变。

## 更省的替代
阶梯，从最便宜的开始：
1. **数据 / 配置**：一张 handler 表就是参数化 invoker 的全部。`Record<SlotId, Command>` / Python `dict[str, Callable]` / Node 配置驱动的 handler map —— 配置决定哪个 key 触发什么。
2. **闭包 / 函数参数**：`var onPress: () -> Void`、TS `onClick={handler}`、`functools.partial`、Java `Runnable`。单方法需求就用函数值；命令对象 ≈ 闭包这层等价是泛化（非本书，本章没有 lambda 对照）。
3. **单个注入对象 / 服务方法**：把 receiver 注入好，命令位只放一个绑定值（`{ execute }` 绑住 service），不建类层次。
4. **才轮到命令对象**：需要 **undo() / 身份与相等 / 序列化（日志、队列、跨重启重放）/ 多个参数共享同一个 receiver / 组合成宏** 中任一项。
不能降级的理由：闭包不能被枚举成历史、不能序列化后再调、不能承载 `undo()` 的旧状态；一旦要"存起来—倒回去—重放"，操作必须是带状态的**值**，而且必须是可按 key 存取的具名对象。

## 最小骨架
**伪代码（角色与方向）**
```
Client ──构造──▶ ConcreteCommand(receiver, args)   ← 变化点：绑哪个 receiver
Invoker ──持有──▶ Command[] slots / history        ← 只调 execute()，不认识 Receiver
Command ──委托──▶ Receiver（厂商类保持原样，不加方法）
undo() = 反着放 execute()，用 execute() 里抓到的 prev 状态
```
**Java**
```java
interface Command { void execute(); }                            // 契约只有一个方法，别加宽
class NoCommand implements Command { public void execute() {} }   // 空槽位的 null object
class CeilingFan {                                                 // Receiver：厂商类保持原样，不加方法
    enum Speed { OFF, LOW, MED, HIGH }
    private Speed speed = Speed.OFF;
    void high() { speed = Speed.HIGH; } void med() { speed = Speed.MED; } void off() { speed = Speed.OFF; }
    Speed speed() { return speed; }
}
class FanHighCommand implements Command {                          // dumb command：只委托
    private final CeilingFan fan;
    private CeilingFan.Speed prev;                                 // undo 用的旧状态，execute 里抓
    FanHighCommand(CeilingFan fan) { this.fan = fan; }
    public void execute() { prev = fan.speed(); fan.high(); }
    void undo() {
        if (prev == null) return;
        switch (prev) { case HIGH: fan.high(); break; case MED: fan.med(); break; default: fan.off(); }
    }
}
class Remote {                                                     // Invoker：只存槽位与历史
    private final Command[] slots = new Command[7];
    private final java.util.Deque<Command> history = new java.util.ArrayDeque<>();
    Remote() { java.util.Arrays.fill(slots, new NoCommand()); }
    void press(int i) { slots[i].execute(); history.push(slots[i]); }
    void undoLast() { Command c = history.poll(); if (c instanceof FanHighCommand) ((FanHighCommand) c).undo(); }
}
```
**Swift**
```swift
// ↓↓↓ 配套，不是模式内容
final class CeilingFan {                                  // Receiver：厂商类保持原样
    enum Speed { case off, low, med, high }
    private(set) var speed: Speed = .off
    func high() { speed = .high }; func med() { speed = .med }; func off() { speed = .off }
}
struct NoCommand: Command { func execute() {} }            // 空槽位的 null object

protocol Command { func execute() }                        // 契约只有一个方法，别加宽
final class FanHighCommand: Command {                      // dumb command：只委托
    let fan: CeilingFan
    var prev: CeilingFan.Speed?
    init(fan: CeilingFan) { self.fan = fan }
    func execute() { prev = fan.speed; fan.high() }         // 先抓旧状态，再改
    func undo() { switch prev { case .high: fan.high(); case .med: fan.med(); default: fan.off() } }
}
final class Remote {                                       // Invoker：只存槽位与历史
    var slots: [Command] = Array(repeating: NoCommand(), count: 7)
    var history: [Command] = []
    func press(_ i: Int) { let c = slots[i]; c.execute(); history.append(c) }
}
```
**TypeScript**
```ts
type Command = { execute(): void; undo?(): void }   // 窄接口，dispatch 表可穷尽
const noCommand: Command = { execute: () => {} }    // 空槽位的 null object
class Remote {
  slots: Command[] = Array(7).fill(noCommand)
  history: Command[] = []                            // 有界：见下节
  set(i: number, c: Command) { this.slots[i] = c }
  press(i: number) { const c = this.slots[i]; c.execute(); this.history.push(c) }
  undoLast() { this.history.pop()?.undo?.() }         // 栈顶倒放，不是重跑 execute
}
```

## 上了之后要盯的代价
- 接口膨胀 = 解耦归零：往 Command 加第二个方法（"让调用方能查设备状态"）之后，invoker 重新开始 instanceof 具体命令。`execute()` 就是全部契约（p.241-242 / p.248）。
- undo 必须是**镜像反操作**：不能靠"带个 flag 重跑 execute()"实现，也不能把 undo 逻辑放在按按钮的 UI 层（p.254-255）。
- **先抓状态再改**：风扇从 medium 调到 high，undo 要回 medium；把反操作硬编码成 off 就是错的（p.258-259）。
- 历史栈：单层 last-command 换成栈（push 每个执行过的命令、undo 时 pop 并调 `undo()`），但要**限深度**，并在命令被重绑/会话重置时清空（p.265 FAQ）。
- 快照钉住的内存归你：每个可撤销命令都持有 receiver 状态，有时是整个集合、文件 blob、打开的行。别每个按键存一份完整对象拷贝；存 diff、限深度、该丢多层时就丢（p.258-259 / p.265 / p.267 的状态保持成本；"看像缓存的泄漏其实是 undo 栈"，非本书）。
- 共享命令的别名 bug：两个槽位包同一个 receiver、或同一个命令实例注册两处，而 prev 存在命令实例里 + 只有一个 undo 槽 → undo 恢复错状态。快照应进 history 条目（按 receiver 身份键），别让命令对象自己当自己的历史（p.260-261）。
- 宏命令的顺序账：`execute()` 顺序遍历，`undo()` **反序**遍历；子项并行只在顺序无关时允许（p.262 / p.271）。
- 硬编码宏是退化的宏：新写一个 `PartyCommand` 里固定调 lightOn/stereoOn/tvOn，等于把弹性删掉还加了新代码；成员应由配置在运行时组装（p.265 FAQ）。
- 队列/线程池：N 个线程 bound 并发、生产者不知道跑的是什么，但别把持有活实体引用的命令序列化后跨重启，也别假设队列顺序就是因果顺序（p.266）。
- 日志重放：非幂等或时间敏感的命令重放前要有闸门；每钉进序列化的一个字段都变成长期兼容负担（p.267）。
- Receiver 保持不动才是收益：外部 SDK / vendor 类不要为了你的接口去改或 fork，胶水写成小命令类，第三方可以自带命令而不碰你的 invoker（p.232 / p.253）。

## 形近模式判别
- vs 闭包 / 回调 / listener / middleware `next()`：单方法接口就是命令形 seams（非本书：这层等价是把 p.241 的一方法契约推广到本章之外）。决定性问题 —— **这个值要不要被存进历史、日志或队列**？要 → 命令对象；只是"稍后跑" → 闭包。
- vs 自己新写一个类硬编码调用其他命令：决定性问题 —— **成员是配置出来的还是写死的**。
- vs Adapter：接外部 SDK 时决定性问题 —— **要改的是接口形状，还是加一个可存可放的调用值**。Receiver 原样不动、胶水放命令侧。
- dumb vs smart command：决定性问题 —— **还有别的 receiver 能复用这段逻辑吗**。没有就是 smart，一旦有就把服务抽出去。

## 组合与框架替身
- 常与组合（MacroCommand 就是一个持有命令数组的 Command）、工厂/组合根（构造命令并绑 receiver）、Null Object（NoCommand，本章列为荣誉提名，p.252）搭配。
- 现代替身（非本书）：Swift `Button(action:)`、target/action、`completion: @escaping () -> Void`、`OperationQueue`；TS/React `addEventListener`、Redux thunk 与 `past/future` action 数组（json-patch / immer patch 做 delta）、`AsyncQueue`；Node BullMQ、Python Celery、Java `ExecutorService.submit(Runnable)` —— Runnable 正是这个形状。事件溯源 / write-ahead log 已经是"记命令 + 按序重放"的成品，别自己再造一套 store/load。

## 决策问句
1. 触发方和工作方是不是**各自**会变？只有一边变 → 一个函数值/一张表，不需要四角色。
2. 有没有人或系统能请求"撤回来上一步"？没有就别加 undo 与状态快照。
3. 这个动作要不要被排队、序列化、日志重放？要 → 它必须是值，命令对象才是对的选择。
4. 快照该存在哪：命令实例里还是 history 条目里？两处都可能，就要防共享实例的别名 bug。
5. invoker 现在能不能不看具体类就加一个新集成？不能 → 抽象泄漏了，回到 `execute()` 单方法契约。

## 证据
- 源文件：《Head First Design Patterns》1st ed.（Eric Freeman & Elisabeth Freeman, with Kathy Sierra & Bert Bates；O'Reilly, 2004）电子版，第 6 章，书页 pp.191-234。换算：正文 PDF 页 = 书页 + 38。
- 书页区间：开场与解耦主张 p.229、p.234；Cubicle Conversation（类型链反模式）p.233；餐厅到模式的映射与配对练习 p.239-240；Command 接口 p.241；SimpleRemoteControl / setCommand p.242；定义与参数化 p.244；类图 p.245；RemoteControl 七个槽位 p.248；vendor 写命令类 p.253；NoCommand 与 null object p.252；undo 与镜像反操作 p.254-256；风扇状态抓取 p.258-259；共享 receiver 的 undo 测试 p.260-261；MacroCommand p.262-264；FAQ（历史栈、PartyCommand、dumb vs smart）p.265；队列与线程池 p.266；日志/重放/事务 p.267；要点 p.268；宏的 undo 答案 p.271。
- 标了（非本书）的条目：命令对象与闭包/lambda 的等价判据、单方法接口即 callback/handler 的推广（含 Swing ActionListener 属第 2 章而非本章）、"看像缓存的泄漏其实是 undo 栈"的经验说法、以及全部现代框架替身（Redux thunk / immer patch、OperationQueue、BullMQ / Celery / ExecutorService、事件溯源与 WAL）。
- distill 中 `INFERRED: yes` 的两行已在正文对应句末标注（非本书）。
