# Observer（中文：观察者，第 2 章）

## 它吸收什么变化
- 变化轴：**谁在依赖这份状态**。订阅者的数量、类型、上线时机都在变；"被通知"这件事的形状不变（一个 `update()`）。
- 不变的部分：状态只有一个所有者。第 2 章里 `WeatherData` 独占测量值，它负责变更并广播，显示件只消费不拥有。
- 搬走的一半：把"依赖者是谁"从主体代码搬进注册表；主体只知道"它们都实现了 Observer"，不知道类名、不知道用途。

## 触发信号
- 主体的通知方法里逐点点名协作者：`display1.update(); display2.update(); display3.update()`（第 2 章第一版写法，答案页 p77 列出它的全部失败点）→ 每加一个依赖都要改主体，正是本模式针对的形状。
- 需求写"以后第三方能自己接新的显示/消费端"（Weather-O-Rama 开放 API）→ 需要一个开放注册点，而不是硬编码调用。
- 出现 `addXxxListener` / `removeXxxListener` 配一个回调方法（Swing `JButton` + `ActionListener`，一个按钮挂 angel 和 devil 两个监听者）→ 框架里已经是这个形状，直接注册即可。
- 两个对象开始写同一个字段，或同一段更新逻辑在多个依赖者里被复制 → 先定唯一所有者，其余降为读取方。
- 主体内部开始 `instanceof 具体观察者` 或调用 `update()` 之外的方法 → 松耦合已经破了（把这条判据推广到一般情况是外推，非本书）。
- 新增依赖者（HeatIndexDisplay）时主体的代码一行没改 → 已经吃到红利，保持注册点开放就是它的正确形态。

## 别上的情形
- 只有一个固定回调、或通知是 1:1：不上＝一个函数字段；上了＝两个接口加一张列表要维护。第 2 章自己说闭包/回调列表就够，观察者只在"依赖者数量可变"时才值回成本。
- 依赖者编译期就定死、永不增删的内部脚本（固定两个协作者）：直接调用更透明，调试路径最短；第 2 章也承认这种场景下硬编码不算缺陷，是开放 API 的要求才让它成为缺陷。
- 真正的多写者数据（协同编辑、多源合并）：单所有者前提不成立，硬套只会把冲突藏进通知链。
- 状态只在读取时才需要、且可以现算：派生选择器或轮询更省，少一层广播。
- "通知"其实是要排队/撤销/参数化的动作：那是 Command 的形状（第 6 章，本文件未取证，非本书）。
- 上了要付的账：接口数量与间接层、顺序不可依赖、退订责任、`update()` 参数被冻成契约。

## 更省的替代
阶梯，从便宜到贵；每级写清什么时候够用、什么时候不够。
1. 声明式订阅表 / 配置：`{ "measurement-changed": handler }`，装配期接线。够：事件源单一、运行期不改线；不够：运行时要增删，或订阅者要按契约提供方法。
2. 一个回调字段（1:1）：`var onDampChanged: ((Double) -> Void)?`、`onChange?: (s: State) => void`。够：只有一个依赖者，或依赖者由父级持有并能保证清理；不够：数量或类型会变。
3. 框架已有的 hub：`NotificationCenter`、`EventTarget`、Node `EventEmitter`、`store.subscribe`。够：只需要"注册 + 广播 + 退订"这套通用机制；不够：你需要控制的正是 `update` 的参数、线程模型和顺序——第 2 章明说内建机制有帮助，但自己实现往往更灵活。
4. 才轮到 Subject/Observer 类结构：未知的外部实现要按共同契约接入，且主体必须完全不知道它们是谁。
   不能降级的原因：契约（`update()`）与生命周期（注册/退订）都要对外开放；匿名闭包列表不带共同类型，也没有稳定的句柄可退订（句柄这一点属现代判断，非本书）。

## 最小骨架
**伪代码（角色与方向）**
```text
interface Observer { update() }                       # 参数越少，契约越稳
interface Subject { registerObserver(o); removeObserver(o); notifyObservers() }
class WeatherData : Subject {                         # 状态的唯一所有者
    measurementsChanged() -> notifyObservers()         # 唯一广播点，不点名具体类
    getTemperature() / getHumidity() ...               # pull 用的窗口
}
class Display : Observer, DisplayElement {            # 两个角色分开：被通知 / 呈现
    ctor(subject) { subject.registerObserver(self); keep(subject) }  # 存引用为了退订和 pull
    update() { 取自己需要的字段; display() }
}
```

**Java**
```java
interface Observer { void update(); }                       // 参数越少，契约越稳
interface Subject {
    void registerObserver(Observer o); void removeObserver(Observer o); void notifyObservers();
}
interface WeatherSource { double getTemperature(); }         // pull 用的窗口
class WeatherData implements Subject, WeatherSource {
    private final java.util.List<Observer> observers = new java.util.ArrayList<>();
    private double temperature;                              // 状态的唯一所有者
    public void registerObserver(Observer o) { observers.add(o); }
    public void removeObserver(Observer o) { observers.remove(o); }
    public void notifyObservers() {
        for (Observer o : new java.util.ArrayList<>(observers)) o.update();  // 走副本：不许在通知里增删
    }
    void measurementChanged() { notifyObservers(); }          // 唯一广播点，不点名具体 Display 类
    public double getTemperature() { return temperature; }
    void setTemperature(double t) { this.temperature = t; measurementChanged(); }
}
class Display implements Observer, WeatherSource {
    private final WeatherSource source;                        // 存引用：为了退订，也为了 pull
    Display(WeatherSource source) { this.source = source; }
    public void update() { double t = source.getTemperature(); System.out.println(t); }  // 取自己需要的字段
    public double getTemperature() { return source.getTemperature(); }
}
```
**Swift**
```swift
protocol Observer: AnyObject { func update(from: WeatherSubject) }   // 契约只有一个方向
protocol WeatherSubject { var temperature: Double { get } }          // pull 的窗口

final class WeatherData: WeatherSubject {
    private var observers: [ObjectIdentifier: Observer] = [:]        // 键便于退订
    private(set) var temperature = 0.0
    func register(_ o: Observer) { observers[.init(o)] = o }
    func remove(_ o: Observer) { observers[.init(o)] = nil }
    func set(_ t: Double) { temperature = t; measurementsChanged() } // 单一所有者
    private func measurementsChanged() { observers.values.forEach { $0.update(from: self) } }
}
```
**TypeScript**
```ts
type Unsubscribe = () => void;
interface WeatherEvent { readonly kind: "measurement-changed" }   // 薄通知，不塞字段

class Subject {
  private listeners = new Set<(e: WeatherEvent) => void>();
  subscribe(l: (e: WeatherEvent) => void): Unsubscribe {           // 退订句柄是契约一部分
    this.listeners.add(l);
    return () => { this.listeners.delete(l); };
  }
  emit(e: WeatherEvent) { for (const l of [...this.listeners]) l(e); }  // 不依赖注册顺序
}
```

## 上了之后要盯的代价
- **顺序不可依赖**：第 2 章换过通知机制后，同一批显示件的输出交错就变了；测试断言"A 先于 B"＝把实现细节钉进契约。顺序真是需求时就显式化（序号、阶段、管道），绝不靠注册顺序。
- **`update()` 的参数就是契约**：把 temp/humidity/pressure 全塞进签名，以后每加一个状态都要改接口和所有观察者；但退化成 `update(Any)` 是把类型安全换成到处强转（这是第 2 章 Brain Power 与 fireside chat 的取舍）。
- **push 会复制状态进观察者**：每个观察者缓存一份字段，带来陈旧风险和签名抖动；pull 保留主体引用现读，代价是多轮取值和更宽的内部可见面。书里认为 pull 更正确，生产上常见混合——推提示/ID，拉重数据。
- **存了主体引用又忘退订＝泄漏**：第 2 章明确建议观察者保留 Subject 引用（为了退订和 pull）；而"强引用 + 忘记退订会把观察者连同整张对象图留下"属机制外推，非本书。框架替身里同一账：`NotificationCenter` 的 block 观察者强捕获 self、`EventEmitter` 不 `off` 就一直活着、React 订阅必须写在 effect cleanup（非本书）。
- **松耦合的价格**：间接层和接口数量；一对永远一起变的协作者之间不值得（第 2 章把这笔账写在 pp.52-53）。
- **链式通知会成环**：一个对象既是观察者又是主体（第 2 章 Ron 那段），一旦 A→B→A 就是无限更新和中间态脏读；DAG/成环分析与"在一条边上断开"的处方是推广，非本书。
- **自己实现主体＝自己承担硬问题**：第 2 章说手写更灵活，但线程安全的监听者列表、单个观察者抛异常不吞掉其余、迭代中退订这些具体账本文件未取证（非本书）。
- **通知与呈现别糊在一起**：`update()` 里直接调 `display()` 是第 2 章自己承认的简化；UI 的真实边界留给后续 MVC。

## 形近模式判别
- 回调字段 vs Observer：订阅者的数量与来源会在运行期变吗？不变就留一个函数。
- Delegate / target-action vs Observer：只有一个接收者还是一个集合？第 2 章指出 delegate 就是"恰好一个观察者"的同形简化。
- 事件总线 / Mediator vs 交叉注册：N 个主体 × M 个观察者互相注册时，判"扇出该由谁拥有"（非本书）。
- Strategy vs Observer：换的是"怎么做"还是"谁被告知"？前者抽行为，后者抽依赖集合。

## 组合与框架替身
- `java.util.Observable` 的暗面（第 2 章 p71）：它是类不是接口，必须被继承，已有父类的对象接不了；`setChanged()` 是 protected，组合不出来；没有接口就换不了实现。（它后来被废弃这件事不在本书取证范围内——非本书。）
- `setChanged()` 本质是合并闸门：不调它就一句都不通知，通知后标志被清除；用途是把"每变 0.1 度就报"节流成"过半度才报"。不需要节流时手写主体更安全。
- 常配：`DisplayElement` 这类第二角色接口（通知与呈现分离）；注册点对外开放时，加行为＝加观察者，主体不改（第 3 章 p87 把观察者列为 OCP 的实例）。
- 现成形状：Swing/AWT listener、JavaBeans `PropertyChangeListener`、RMI（第 2 章列举）；现代对应 `NotificationCenter` / Combine、`EventTarget` / `EventEmitter` / RxJS Subject / Zustand subscribe、Python blinker 与 Qt signal-slot（非本书）。

## 决策问句
1. 依赖者的数量或类型会在运行期变吗？不会 → 一个闭包字段就够。
2. `update()` 要带几个参数？超过两个原始值，就要回答"我在 push 还是在焊接口"。
3. 观察者能干净退订吗？谁存主体引用、谁保证清理一定发生（含 deinit / useEffect cleanup）？
4. 有没有任何东西依赖通知顺序——测试、输出、派生值？有就用显式排序机制，不靠注册顺序。
5. 平台自带的 observable 会不会强迫继承、锁死 `update` 参数或线程模型？会 → 自己写一个薄主体，并接住随之而来的并发与异常隔离。

## 证据
- 源文件：《Head First Design Patterns》1st ed.（Eric Freeman & Elisabeth Freeman, with Kathy Sierra & Bert Bates；O'Reilly, 2004）电子版，第 2 章，书页 pp.37-78。换算：正文 PDF 页 = 书页 + 38。
- 本书依据：订阅/退订类比 pp.44-47；模式定义与五幕剧 p.51、pp.48-51；一对多与依赖关系、松耦合 pp.52-53；`WeatherData` 实现 `Subject` pp.55-58；类图与 `DisplayElement` 角色 p.56；"手写往往更灵活" p.57；`update` 参数是否明智 p.57；显示件构造存 Subject 引用的理由 p.59；push vs pull fireside chat pp.60-63 与 HeatIndexDisplay 练习 p.61；`java.util` 改写走 getter pp.65-68；`setChanged` 节流 p.66；pull 模式强转具体主体 p.68；换机制后输出顺序变化 p.70；`java.util.Observable` 暗面 p.71；Swing 监听者 pp.72-73；`update()` 契约、顺序、松耦合小结 p.74；第一版硬编码写法 pp.40-42 与答案页 p.77；观察者作为 OCP 例子（第 3 章 p.87）。
- 标了（非本书）的条目：`Observable` 的废弃及其迁移成本；强引用不退订造成泄漏的机制与"弱引用/保证清理"处方；自实现主体的线程安全、异常隔离、迭代中退订；N×M 交叉注册交给事件总线/Mediator；链式通知的 DAG/成环分析；匿名闭包列表缺稳定退订句柄；Command（第 6 章）与 MVC 的对照；Swift/TS/Node/Python 的语言与框架替身。
- 本文件不主张：并发通知模型、事件溯源、背压与重放语义——均不在取证范围内。
