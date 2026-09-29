# Compound Patterns（中文：复合模式与 MVC，第 12 章）

## 它吸收什么变化

单个模式各管一半：Observer 管「谁需要知道」，Strategy 管「这块界面遇到输入怎么解读」，Composite 管「一棵界面树自己画自己」。
复合结构吸收的是「这几处变化在同一类问题里每次一起出现」，于是把角色钉死：模型不认识视图、视图不认识输入语义、控制器不认识领域规则——搬走的是三方之间的引用方向，不变的是数据本身与渲染树结构。
只有当同一组角色在多个不相干模块里反复出现、且每个角色的职责说得清，才配叫复合模式；一次性凑在一张图里只是 cooperating patterns（书里点名的反例是 DuckSimulator）。

## 触发信号

- 同一个组件在一个 diff 里既发请求又格式化领域数据 → 五条消息被并成一条，角色漏了
- 「模型改了显示就跟着改」而显示是一棵嵌套树 → Observer + Composite 同时在场
- 两块界面只差输入的解读方式（同一播放界面既接 MIDI 又接心率） → Controller 是视图的 Strategy
- 有人为了换一个数据源新写了一份视图或改了视图代码 → 该写的是模型 Adapter，不是视图
- 出现「订阅一个组/文件夹/账号」而不只订阅单个实体 → Composite 的注册要沿子树扇出
- README/文档写着 "MVC"，而你要预测某个改动落在哪 → 按角色审（谁是 Subject？策略被组合了吗？视图是树吗？）
- 你只说得出模式名，说不出它这次吸收哪个具体变化 → pattern-first，本章的头号反模式，停

## 别上的情形

- 一屏、一个数据源、没有第二个消费者 → 不上只是直接渲染；上了要多付三层文件跳转和一次角色追问
- 为了「可扩展」把 Abstract Factory + Decorator + Observer 一起堆上（书中承认有几个当时就是过头）→ 不上没有损失；上了要维护包装与注册，而需求只是「数一下调用」
- 文档里把临时凑的形状写成「复合模式」 → 它掩盖了谁观察谁，后人无法复用这个形状
- 服务端一次响应、无客户端连接，需求却写「变了就更新显示」 → 别在服务端内存挂 observer 列表等浏览器反应；请求周期形状本来就放弃了活观察，先决定陈旧可不可接受
- 控制器代码九成是「读字段 A、写字段 B」 → 用平台绑定层，别手写胶水，也别为它再造一个模式
- ORM entity 同时充当 Subject、策略位与渲染对象 → 那不是复合，是三种角色没分家

## 更省的替代

逐级确认上一级不够再升级：

1. 数据/配置：路由表 + 每请求一次查询（Model 2 形状就是「角色不变、传输换成响应」）；导航态放 URL 而不是建 store（非本书）
2. 闭包/函数参数：视图收一个 `onStart: () -> Void` 就是 Strategy 位——换解读不新建组件。只有当解读规则跨多个方法、要在构造期注入并被测试替换时，才升成 ControllerInterface 对象（非本书）
3. 单个注入对象：把 register/notify 封进一个 Observable helper，由各 Subject 组合使用（书里就是 QuackObservable + Observable + 委托）；视图树与遍历交给平台组件层级——Composite 和 Iterator 本章一行代码都没写（非本书的推广）
4. 才轮到完整三角色：当「同一模型要被多个可替换视图消费」**且**「同一视图要被多种输入解读复用」同时成立。它降级不掉，因为角色分离买的就是替换权：notify 闭包没有注册/退订的生命周期，纯组件树没有独立于 UI 的规则源，两者都不够让新模型接旧视图。

## 最小骨架

**伪代码（角色与方向）**
```
Model      : Subject        // 数据 + 状态 + 应用规则，并且拥有时钟/更新循环
             register/notify (Observer) → 视图列表，允许多个视图
View       : Composite      // 嵌套显示组件，自己递归画自己；只暴露 enableX/disableX/show(v)
Controller : View 的 Strategy // 创建视图、把自己塞进视图、把输入解读成模型调用
             可注册成模型 observer，用来决定控件可用性（而不是让视图自己推断）
五条消息：用户→视图；视图→控制器「我收到了什么」；控制器→模型「改状态」；
          控制器→视图「启用/禁用」；模型→视图「变了」→ 视图回头拉状态
只有这五条箭头；加第六条就在扣视图复用
```

**Java**
```java
interface Observable { void addObserver(java.util.function.Consumer<PlayerModel> view); void notifyObservers(); }
class PlayerModel implements Observable {                          // Subject：数据 + 状态 + 应用规则
    private final java.util.List<java.util.function.Consumer<PlayerModel>> views = new java.util.ArrayList<>();
    private int bpm = 0; boolean isPlaying = false;
    public void addObserver(java.util.function.Consumer<PlayerModel> view) { views.add(view); }
    public void notifyObservers() {
        for (java.util.function.Consumer<PlayerModel> v : new java.util.ArrayList<>(views)) v.accept(this);
    }
    void tick() { bpm += 1; notifyObservers(); }                    // 模型自己驱动循环并 notify，视图不轮询
    int bpm() { return bpm; }                                       // 只读面：视图拿不到写接口
}
interface Panel { void render(); }                                   // View = Composite：嵌套组件自己递归画
class PlayerPanel implements Panel {
    private final PlayerModel model; private final java.util.List<Panel> children = new java.util.ArrayList<>();
    PlayerPanel(PlayerModel model) { this.model = model; }
    Panel add(Panel p) { children.add(p); return this; }             // 只暴露原语：add / render
    public void render() {
        System.out.println("BPM " + model.bpm());                    // notify 之后 pull
        for (Panel c : children) c.render();
    }
}
class BeatController implements java.util.function.Consumer<PlayerModel> {   // View 的 Strategy
    private final Panel view;
    BeatController(PlayerModel model, Panel view) { this.view = view; model.addObserver(this); }
    public void accept(PlayerModel m) { view.render(); }              // 被通知只为决定呈现，不算阈值
    void didTapStart(PlayerModel m) { m.isPlaying = true; }           // 输入解读成模型调用
}
```
**Swift**
```swift
import SwiftUI                                            // 平台视图层 = Composite 的一侧
import Observation                                        // @Observable 宏，替掉手写 notify

protocol PlayerSnapshot { var bpm: Int { get } }           // 只读面：视图拿不到写接口

@Observable final class PlayerModel: PlayerSnapshot {     // Subject：规则与状态都在这层
    private(set) var bpm = 0
    var isPlaying = false
    func tick() { bpm += 1 /* 模型自己驱动循环并从循环里 notify；视图不轮询 */ }
}
struct PlayerView: View {                                 // Composite：只画 + 暴露原语
    let snapshot: PlayerSnapshot
    var body: some View { Text("BPM \(snapshot.bpm)") }   // notify 之后 pull
}
struct BeatController {                                   // View 的 Strategy
    let model: PlayerModel                                // 它建视图、把自身配进去
    func didTapStart() { model.isPlaying = true }         // 只解读输入，不算阈值
}
let view = PlayerView(snapshot: PlayerModel())
```
**TypeScript**
```ts
// ↓↓↓ 配套，不是模式内容
const clamp = (v: number) => Math.min(200, Math.max(40, v))   // 应用规则：住这里，不住组件里

type Msg = { type: 'start' } | { type: 'setBpm'; value: number }
type State = { bpm: number }
// 箭头 1-2：视图只 dispatch（组件树 = Composite）
// 箭头 3：reducer / 域模块改状态——clamp 是应用逻辑，必须住这里而不是组件里
function beatReducer(s: State, m: Msg): State {
  return m.type === 'setBpm' ? { ...s, bpm: clamp(m.value) } : s
}
const selectBpm = (s: State) => s.bpm          // 箭头 4-5：selector 驱动重渲染
// 新数据源接进来：写一个 adapter selector 映射进现有 state shape，不动组件
```

## 上了之后要盯的代价

- 每多一条箭头（视图直接写模型、模型认识某个视图类型）就扣一分视图复用；书里承认给视图完整写接口是「为了简单」并直接标危险——便宜修法是只读协议/DTO，不是靠纪律
- God controller：规则 + 格式化 + 持久化挤进控制器 → 一个类三个变化原因，且离不开 UI 就没法单测；第二块界面靠复制它的逻辑复用，就是把规则源拆成两份
- Anemic model：模型只剩 getter/setter，条件全在控制器与视图 → 盒子标签还在但复合的收益（可换视图、单一规则源）归零（非本书的标签）
- 空实现 Adapter 留下能点但没反应的控件：要么视图侧禁掉它，要么把能力差异显式放进接口；静默 no-op 一个破坏性操作是最坏的一档
- 双重通知或漏通知：Composite 与叶子都 emit，或只在根上挂一份 observer 列表 → 一次变更触发 N 次回调或干脆收不到
- 装饰器包住了可观察对象却没转发 register/notify：订阅看着成功，回调一个都不来
- 更新循环有两个驱动者：视图起 timer 读模型状态，等于重建了视图→模型的知识并引入竞争时间源；本章的模型自己跑循环（meta 回调重启 sequencer、心率模型自起线程）
- 推 vs 拉选错：把整个模型广播给只关心一个字段的观察者，是观察者模式那章就点过的毛病；本章经典路径是 notify 之后视图自己 get，只有载荷小而固定且人人都要时才推
- 按框架名词推断角色会判错：同一个 MVC 名下实现差别很大（Swing 式 / Model 2 / 浏览器渲染），Model 2 的视图什么都不注册
- 视图树上的 add()/注册接口要么只给 Composite（安全：叶子压根没有它），要么给共享组件接口（透明：客户端不区分叶与枝）；两头不靠最贵——透明的接口里叶子抛 not supported，安全的接口里客户端到处判类型

## 形近模式判别

- 复合模式 vs 凑一起的模式堆：决定性问题——同一组角色在两个不相干模块里都出现、且每个角色的职责能一句话说清吗？
- MVC vs MVVM / Service Dispatcher / View Handler：决定性问题——notify 路径真的存在吗（谁是 Subject）、输入解读是被组合进视图的对象还是外部调度器？后三个名字不在本章抽取范围内，别给它们挂书页（非本书）
- Observer vs Mediator：决定性问题——状态变化广播给任意多方（Observer），还是一个协调者持有全部协调规则（Mediator，见附录）？
- Controller-as-Strategy vs 视图内条件分支：决定性问题——换掉输入解读要不要新建组件？要，说明策略根本没抽出来
- 策略位 vs 模板方法：决定性问题——这块行为是运行时组合进来的还是被子类覆写死的？

## 组合与框架替身

- 本章的复合就三件：Observer（模型↔视图）+ Strategy（控制器是视图的策略）+ Composite（视图是树）；再加两条常用外挂：Adapter 让旧视图旧控制器活过新模型（控制器在交给视图前把它包上）；Composite + Observer 让注册沿子树扇出、叶子自己通知、Composite 的 notify 是空实现
- 常叠栈：Adapter + Decorator + Abstract Factory——工厂发「已包好」的产物；把裸对象和包好的对象从同一个 API 发出去，漏包那条路径的计数/埋点/鉴权会静默消失
- 平台已经给了替身，直接复用而不是 fork：本章零代码地用了 Swing/AWT 的组件嵌套和集合框架的 Iterator；现代对应 SwiftUI/AppKit 视图树 + `@Observable`/Combine、React 树 + Redux/Zustand 的 store 与 selector、domain-event bus、SSR/RSC 的请求生命周期（均非本书）。平台已经实现的 Subject/Composite 机制就拿来用，自己重写等于把它后续的修复分叉走
- 绑定层（Interface Builder/Combine/SwiftUI 绑定）替掉的是控制器那种「读 A 写 B」的胶水；只让绑定走读路径，写路径仍要经控制器，否则视图又认识了模型内部（非本书的表述）
- 后端同形：domain event = Subject，请求处理器 = Strategy 位，模板/DTO 渲染 = Composite；破坏点是 entity 一人分饰三角

## 决策问句

1. 这组角色在别的不相干模块里也出现过吗？没有就别在文档里叫它复合模式。
2. 五条消息各自落在谁身上？现在有没有第六条（视图写模型 / 模型认识视图类型）？
3. 阈值、计价、状态迁移这些规则此刻住在哪一层？在控制器或视图里就搬回模型。
4. 谁驱动更新循环？视图里有没有 timer 在读模型状态？订阅在树上会不会被通知两次？
5. 这个框架自称 MVC：它的 Subject 在哪、策略被组合进视图了吗、视图是 Composite 吗？（Model 2 / 纯 SSR 答不出第一问）

## 证据

- 源文件：《Head First Design Patterns》1st ed.（Eric Freeman & Elisabeth Freeman, with Kathy Sierra & Bert Bates；O'Reilly, 2004）电子版，第 12 章，书页 pp.499-576（抽取止于 p.576 的 ready-bake DJ 代码）。换算：正文 PDF 页 = 书页 + 38。
- 页区间：复合模式定义 p.500；Duck 栈与漏包 pp.504-511、p.515、p.521、p.523；QuackObservable/Observable pp.516-518；pattern-first 与 DuckSimulator 反例 p.522；控制器胶水与绑定 p.526-527；MP3 例 p.529；五条消息 pp.530-531；角色图 pp.532-533；setBPM 通知 p.538；ControllerInterface 与 DJView 构造 pp.542-544；HeartAdapter 与空方法 pp.545-548；Model 2 流程 pp.549-554（含 p.550 分工）、p.556、p.557-558、p.559；更新循环 p.566、p.574；收尾清单 p.560；练习解 pp.561-562；平台代给 Iterator/Composite p.513、p.540、p.569
- 书中明说：MVC = Observer + Strategy + Composite；控制器是视图的策略并负责创建视图；视图是 Composite、事件后回拉状态；应用逻辑归模型、视图不改模型；Model 2 用 servlet 做控制器、JSP/HTML 做视图、bean 随请求传递，逐请求之外的通知拿不到；DuckSimulator 是刻意凑的不算复合；Flock 注册扇出而 notify 为空；QuackCounter 必须转发 register/notify；空 Adapter 留下无效按钮；漏包就没有装饰行为；Iterator 与 Swing 嵌套由平台提供
- 标了（非本书）的条目：MVVM / ViewModel / Service Dispatcher / View Handler / 模板方法式视图遍历 / 双缓冲 / 事件冒泡（均不在本章抽取内，故不给页号）；SwiftUI `@Observable`、Combine、Redux/Zustand、selector/normalizer、RSC/SSR、domain-event bus、六边形防腐层等全部现代映射；"anemic model" 这个标签；「平台已给角色就复用、别 fork 其修复」与「绑定层替代控制器胶水」这两条一般化判据
