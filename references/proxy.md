# Proxy（中文：代理，第 11 章）

## 它吸收什么变化

变化轴是「调用怎样抵达真实对象」：对象可能在另一个地址空间、还没被建出来、结果值得复用、或调用者没资格直接碰它。
不变的是客户端的调用签名——代理与真实对象实现同一个 Subject 接口，调用处一行不改。
本模式把「是否放行 / 何时创建 / 结果从哪来」这一半决策从业务代码搬进一个同接口的壳，并且壳可以拥有被包对象的生老病死。
接口一致是定义级约束：改了接口的壳就不是代理而是 Adapter。

## 触发信号

- 客户端字段已写成协议/interface（`repo: Repo`），同一调用点要能在本地实现与远端实现间换 → 只有代理能保住签名
- 构造函数耗时无上限（图片、模型文件、DB 聚合、大列表），且创建出来的对象有一部分从没被真正用到 → 虚拟代理
- 循环里对同一 key 反复请求同一个昂贵资源 → 缓存代理（书中：每次选中都重建同一个 ImageIcon）
- 同一份数据，owner 与非 owner 合法可调的方法子集不同 → 保护代理
- 每个方法都以 `if subject == nil` 开头，或方法体外层都是同一段 before/after（计时、日志、重试）→ 该抽状态或抽成一个 handler
- 保护代理已存在，但被保护的具体类在别处仍可 `new`/被导出 → 这是真 bug，访问控制成了布景
- 需求原文是「调 HTTP 服务」「懒加载」「结果缓存住」而调用点本来就用接口 → 框架多半已经给你代理了

## 别上的情形

- 只是想「晚点再建」，没有接口替换需求 → 不上只多写一行 `lazy var`；上了多付一个类、一层间接、断点先落在壳里
- 只有一处权限判断且不区分调用者身份 → 不上是 5 行 guard；上了要维护一个壳和一个工厂收口点
- 跨地址边界只是打包意外（同进程同机器）→ 不上没有损失；上了就把 nanosecond 调用换成会超时、会失败的 I/O
- 已经存在 cache→auth→logging→stub 的多层包裹 → 不上：把职责并到更少命名处或中间件；上了：读一段调用要跳四层，书里对包十层直接判回头重审
- 目的只是把接口对上或把一堆调用简化 → 那是 Adapter / Facade 的活；用代理的名字写它们，后面的人会以为访问被中介过
- 内部小类、单一消费者、没有任何访问问题，只为「以后好替换」 → 理论上的可替换性不值得一个包装类

## 更省的替代

逐级确认上一级不够用再升级：

1. 配置/数据表：`staleTime: 30_000`、`URLCache` 容量与 TTL、`next/image` 的占位尺寸、网关或 DB RLS 的策略表——「复用结果」和「别提前建」多数在这级就结束（非本书）
2. 语言内建：`lazy var subject: RealThing`（延迟构造且接口不变）；Swift 值类型的写时复制就是免费的 CoW 代理（非本书）
3. 闭包/函数参数：`func report(load: () async -> Snapshot)`——把拦截点显式传给调用方，不需要任何类型（非本书）
4. 单个注入对象：一个 `struct Gate<S: Subject>(role: Role, subject: S)`，或 fetch/axios 的一个 interceptor——一条横切关注点一个壳，够用
5. 才轮到代理类：当「客户端字段必须能被换成另一个实现」**且**「访问被真正中介（创建时机/权限/寻址）」同时成立。这不能降级到 1-3，因为数据表和闭包都改不了调用点的类型声明，也无法把 subject 的生命周期所有权交给一个和被包对象同签名的替身。

## 最小骨架

**伪代码（角色与方向）**
```
Subject  = request(ctx) -> Result          // 客户端只认这个签名
Real     = 昂贵 / 远端 / 受保护的真正实现
Proxy    : Subject                          // 唯一新增物
  state: subject: Subject?                  // 可以还不存在
  state: role, cacheKey, endpoint
  request(): gate(role) → reject 或放行
             subject ??= create/connect     // 代理拥有创建，decorator 做不到
             return subject.request(ctx)
Client   field: Subject                     // 永不写具体类
Factory  makeSubject() -> Subject           // 唯一出口，Real 无 public init
```

**Java**
```java
interface MachineReport { String report() throws Exception; }         // 客户端只认这个签名
class RealMachineReport implements MachineReport {
    private final String snapshot;
    private RealMachineReport(String snapshot) { this.snapshot = snapshot; }   // 不暴露 public init
    static MachineReport create(String id) throws Exception {                  // 工厂收口＝保护代理的前提
        return new RealMachineReport(fetch(id));
    }
    private static String fetch(String id) throws Exception { return id + " rack-7 count=3"; }
    public String report() { return snapshot; }                                 // 一次取快照，别逐个 getter 往返
}
class GuardedMachineReport implements MachineReport {                           // 唯一新增物：代理
    private final String role; private final String id;
    private MachineReport subject;                                               // 可以还不存在
    GuardedMachineReport(String role, String id) { this.role = role; this.id = id; }
    public String report() throws Exception {
        if (!"ops".equals(role)) throw new SecurityException("denied: " + id);    // 拒绝要抛，别静默返回默认值
        if (subject == null) subject = RealMachineReport.create(id);              // 代理拥有创建，decorator 做不到
        return subject.report();                                                  // 只转发一层，不再叠壳
    }
}
```
**Swift**
```swift
import Foundation
// ↓↓↓ 配套，不是模式内容
struct Machine { let location: String; let count: Int }
enum TransportError: Error { case notReady }
func fetchMachine(_ url: URL) async throws -> Machine { Machine(location: "rack-7", count: 3) }

protocol MachineReport: Sendable { func report() async throws -> String }

actor RemoteMachineReport: MachineReport {               // actor：把惰性填充串行化
    private let endpoint: URL
    private var pending: Task<Machine, Error>?            // 代理持有生命周期
    init(endpoint: URL) { self.endpoint = endpoint }
    func report() async throws -> String {
        let url = endpoint                                // 先取快照再交给 Task，避免跨隔离
        if pending == nil { pending = Task { try await fetchMachine(url) } }
        guard let task = pending else { throw TransportError.notReady }
        let m = try await task.value                       // 失败必须抛，不吞成默认值
        return "\(m.location) \(m.count)"                 // 一次取快照，别逐个 getter 往返
    }
}
// 客户端：let r: MachineReport = factory()  —— 看不见 RemoteMachineReport
// 保护代理靠工厂收口：具体实现不对外暴露 init，否则门控是布景
```
**TypeScript**
```ts
// ↓↓↓ 配套，不是模式内容
type Row = { id: string }
class PermissionError extends Error { constructor(id: string) { super(`denied: ${id}`) } }

interface Repo { load(id: string): Promise<Row> }

function proxied(make: () => Promise<Repo>, gate: (id: string) => boolean): Repo {
  let inst: Repo | null = null                           // proxy owns lifecycle
  return {                                              // 同一个 interface，调用点无感
    async load(id) {
      if (!gate(id)) throw new PermissionError(id)       // protection：拒绝要抛，别静默
      const r = (inst ??= await make())                  // virtual/lazy：首次才真建
      return r.load(id)                                  // 只转发一层，不再叠壳
    },
  }
}
```

## 上了之后要盯的代价

- 远程代理保住了方法签名但没保住失败模型：每次调用都是 I/O，接口要声明传输错误，调用方必须处理；把透明远程当成可以完全藏起来的实现细节，就是在部分失败下骗自己
- 细粒度 getter 上网：一个报表对 N 台机器各调 3 个 getter 就是 3N 次往返（书中 monitor 就是这个形状）→ 合并成一个返回快照 DTO 的方法（非本书的一般化）
- 序列化只在运行时炸：边界类型不可序列化、反向引用被标 transient 后在远端读成 null、客户端机器上根本没有代理类，这三类都不在编译期报错
- 异步填充要真同步：书里用一个 `retrieving` 布尔加「只有一个线程会调 paint」的理由，那是 paint 路径的特权而非通用保证；从 completion handler 里写 subject 引用就要正式加锁/串行化；失败别永久缓存成「还在加载」
- 占位代价是用户可见的：硬编码 800x600、"Loading…" 再加一次 repaint，真对象落地即 layout 位移；不预留尺寸的 spinner 是同一个 bug 换了长相
- 每个代理 = 一个类 + 一次间接 + 一个调试落点；栈与断点先落在壳上，动态代理若不能在日志里命名就更难查
- 分支膨胀：`if subject == nil` 每方法每阶段一条，出现第三阶段（failed/expired）时该把阶段抽成 State，让状态自己持有行为
- 按角色成套的保护代理会长出镜像代码（Owner/NonOwner 两个 handler 互为反面），第三个角色一到就重复；规则应收敛到一个 policy 对象或一个拦截器，代理保持薄（非本书的补救）
- 客户端侧门控不是安全：真实对象对任何能拿到它的人仍然可调；安全边界在服务端/网关，那里已经是代理了
- 缓存代理的账换了科目：没有失效策略或容量上限的缓存，把延迟问题变成泄漏问题；命中时的「正确但过期」比未命中时的慢更难发现
- 动态代理的账是命名：不要按方法名前缀分支（书中点名 `startsWith("get")` 这类写法会被 `settle()` 之类击穿并静默落到默认分支），并且 handler 必须能在日志/栈里被叫出名字
- 动物园其余档各有专属失效（书列了 caching/firewall/smart reference/synchronisation/complexity-hiding/copy-on-write）：挡住坏客户端的同时误杀合法流量、引用计数记错、锁竞争、延迟复制的惊讶——动机选一档，就要接住它那一档的失效

## 形近模式判别

- vs Decorator（同接口 + 转发，结构完全一样，只有意图能分）：决定性问题——壳会不会自己创建/销毁被包对象？代理会；decorator 收到的已是建好的实例，所以想延迟构造成本时 decorator 根本做不到
- vs Adapter：决定性问题——接口变了吗？一变就不是代理，哪怕它转发的正是同一个对象
- vs Facade：决定性问题——给出的是「更简单的新接口并放行」还是「原接口但控制访问」？书中承认的 complexity-hiding 代理仍在门控，facade 不门控
- vs 拦截器/中间件/装饰器链：决定性问题——被替换的是客户端字段声明的那个类型，还是只是调用被旁观了一下？

## 组合与框架替身

- 常配：Proxy + Observer（填充完成后通知，而不是让等待方轮询）；Proxy + State（loaded / not-loaded，书末设计练习的解）；Proxy + Strategy（把权限规则注入薄代理）；Proxy + Factory/Abstract Factory（保证没人漏包、没人绕过收口）；跨切面常与 Decorator 同形，按上面的意图判据命名
- 平台已经是代理，直接用它：`React.lazy`/Suspense、`next/image` 占位、ORM 懒加载关系、Hibernate 关联代理 = 虚拟代理；React Query/SWR、DataLoader、service worker、URLCache、CDN = 缓存代理；gRPC/Thrift/tRPC 桩、Prisma、Envoy/Istio sidecar = 远程代理（书的 stub/skeleton 即其前身）；axios/fetch interceptor、nest 装饰器、Spring AOP、Python decorator、OpenTelemetry 自动埋点 = 动态代理；网关鉴权、DB RLS、路由 guard = 保护代理（均非本书）
- 判据：写接口，让平台产代理；只有当你必须接管平台代理的失败语义（重试预算、超时、缓存失效策略）时，才自己写那个类
- 别手写 marshalling、懒加载、事务/安全 socket 样板——书中 RMI 已经替你建好 client/service helper

## 决策问句

1. 客户端能否一行不改地把真实对象换成我的壳？接口若不同，我在写的不是代理。
2. 动机是哪一个——延迟 / 复用 / 跨地址 / 放行 / 埋点？该动机自带的失效（占位位移、缓存陈旧、超时与序列化崩、被绕过、无名的 handler）我打算怎么承担？
3. `lazy`、interceptor、`staleTime`、ORM 懒加载或 codegen 能不能直接产出一个这样的代理？能就别建类。
4. 真实对象还有 public constructor 或别的导出路径吗？没收口的保护代理等于没有保护。
5. 这个壳是第几层？一次用户动作要对同一个代理发几次调用？两层以上就该合并职责，>1 次就该换快照 DTO。

## 证据

- 源文件：《Head First Design Patterns》1st ed.（Eric Freeman & Elisabeth Freeman, with Kathy Sierra & Bert Bates；O'Reilly, 2004）电子版，第 11 章，书页 pp.429-498。换算：正文 PDF 页 = 书页 + 38。
- 页区间：该 distill 只记抽取行号、未记书页。定义与类图 1424-1494；远程代理与 RMI 171-466、570-601、850-901；虚拟代理 ImageProxy 1500-1770、1634-1670、1740-1774、1777-1811；Q&A 与收口工厂 1911-1927、1954-1979、1980-2079、2073-2076；动态代理与 Matchmaker 保护代理 2084-2437、2494-2530、2629-2659、3102-3131；代理动物园 2713-2800、2985-2990；代价清单 3002-3004
- 书中明说：同接口是定义的一部分、代理可创建/缓存/销毁 subject、decorator 从不实例化、用工厂逼客户端走代理、客户端只引用接口、不要多层包裹、RMI 三大部署错误、800x600 占位与 repaint、`retrieving` 布尔的单线程理由、Owner/NonOwner 近乎镜像、代理动物园各动机与代价、"mighty ugly code"
- 标了（非本书）的条目：全部 Swift/TS 具体写法（`lazy var`、property wrapper、actor、`Task` 记忆化、`Proxy()`、useMemo/lazy/staleTime）；所有框架替身（React.lazy、SWR/React Query、DataLoader、Prisma、tRPC、gRPC、Envoy/Istio、AOP、OpenTelemetry、网关 RLS）；细粒度 getter 往返放大的一般化；logging/retry 属书中「其他变体」而非已做示例；收敛到单一 policy 的补救；「代理是杀鸡用牛刀时退到最小工具」这条阶梯本身
