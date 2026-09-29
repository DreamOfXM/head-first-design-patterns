# 给编码 Agent 的设计模式判断力

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Patterns](https://img.shields.io/badge/GoF%2023-covered-teal)](references/) [![Skeletons](https://img.shields.io/badge/examples%20compile-63%2F63-brightgreen)](scripts/examples_check.py)

[English](README.md) | **简体中文**

一份让 AI 编码 Agent 判断**这段代码到底要不要上设计模式**的 [skill](SKILL.md)：如果要，选哪个、停在多低的档位、付出什么代价、以及怎么把它撤回来。内容蒸馏自《Head First Design Patterns》（第一版，O'Reilly 2004），GoF 23 个模式全覆盖。

默认答案是**"这里不需要模式"**，而且整个结构就是逼着把这个答案写下来、给出理由。任何一次"要"，都必须指名它消掉了哪一处分支、或切断了哪一条依赖边。

---

## 这是什么

它不是模式目录，不是教程，也不是"用得多就是好"的记分卡。它是一套对着你的真实文件跑的判断流程：

1. **变化句** — 填空：「**______** 会变；**______** 不变；由 **______** 在 **______**（编译期/构造期/运行期）决定。」填不出来 → 不上模式。
2. **触发表** — 24 行你在代码里真能看见的形状（按类型分支的构造、按状态分支的方法、包装类的构造点、每个 handler 重复的前后置）→ 候选模式，**以及先该试的更省方案**。
3. **最省阶梯 L0–L4** — 直接写 → 数据（枚举/转移表/配置）→ 可注入的函数 → 单个注入对象 → 模式类结构。每升一档必须回答：*这一档把哪个文件变成了只读文件？*
4. **反查闸 8 问** — 第 2 个实现在哪个文件、这条变化是能指名的还是"万一"、间接层数减掉分支数等于几、异常栈能不能看出真实执行者、对象身份还成立吗、谁构造谁在测试里替换、抽象有没有泄漏、**撤掉这层要改几个消费者文件**。

第 1、3、8 问用 `grep`/`git diff` 数出来，不许口算；第 8 问只数消费者，数到 1 或 0 就是这层没买到隔离。命令写在 [SKILL.md](SKILL.md) 里。

另外两件事是一等公民：**[撤掉模式](SKILL.md)**（死扩展点、单实现接口、只有一个产品的工厂）和一份**[模式决策记录模板](SKILL.md)**，放在代码旁边，形如 `docs/adr/NNN-*.md`。

## 明确不覆盖什么

| 你要的是 | 该去用 |
|---|---|
| 复现单点 bug | 常规调试 |
| 这屏界面对不对 | 设计/界面类 skill |
| 要几个服务、多大容量、选哪个库 | 架构选型类 skill |
| 命名、格式、局部清理 | 代码风格类 skill |
| 上线前的验收取证 | acceptance-testing 类 skill |
| 原书正文与图表 | 原书本身 |

## 覆盖范围

| 位置 | 模式 | 深度 |
|---|---|---|
| `references/` 下 11 个章节文件 | Strategy、Observer、Decorator、Factory Method + Abstract Factory、Singleton、Command、Adapter + Facade、Template Method、Iterator + Composite、State、Proxy | 对应原书章节，附页码区间 |
| [`compound-mvc.md`](references/compound-mvc.md) | MVC 作为三个角色的复合 | 第 12 章 |
| [`leftover-patterns.md`](references/leftover-patterns.md) | Builder、Bridge、Chain of Responsibility、Flyweight、Interpreter、Mediator、Memento、Prototype、Visitor | **仅目录深度** — 原书对每个只给速查篇幅；要据此定结构，先回专门来源复核 |
| [`restraint-and-workflow.md`](references/restraint-and-workflow.md) | 三次法则、怎么读一条目录条目、反模式卡 | 第 13 章 |
| [`disambiguation.md`](references/disambiguation.md) | 长得像的模式对，每对一个决策问题 | 跨章节 |

## 骨架代码

每个模式位置带四段：**伪代码角色 → Java → Swift → TypeScript**。Java 是原书自己的语言，但重写成最小骨架（不是书里的例程）；Swift 与 TypeScript 是现代语言映射，形状不同的地方标了 `（非本书）`。

63 段全部逐列真编译过：`javac -d`、`swiftc -typecheck`、`tsc --noEmit --strict`。为了让单段代码能独立编译而补的脚手架类型标了 `// ↓↓↓ 配套`，它们不是模式内容——要么跟骨架一起拿走，要么整段丢掉，别抄一半。

## 机器闸门

```bash
python3 scripts/smell_scan.py <dir or files…>     # 扫你的代码里的结构信号
python3 scripts/smell_scan.py --selftest          # 检波器还能不能分清真假
python3 scripts/examples_check.py                 # 本 skill 自己的例子还能不能编译
python3 scripts/examples_check.py --selftest
```

两个脚本同一退出码契约：`0` 没发现 / 全部编译通过 · `1` 有发现，或有例子编不过了 · `2` **这一轮判不了**（路径不对、文件类型不支持、工具链缺失或装了但跑不起来）。`2` 既不是通过也不是拦截，如实说"未判定"。

skill 自己写明的诚实边界：

- **数字阈值是我加的，不是书里的。** 原书没有任何数字判据。计数只决定"值不值得人看一眼"。
- `smell_scan.py` 是正则级、不是 AST：宏、代码生成、动态派发、跨行条件会漏，报告里会这么说。
- 它有意过滤框架与值类型（`Button`、`URLSession`、`struct` 构造、点号修饰链）。这些排除是设计决策，不是"已验证干净"。
- 两个真实项目上的校准：16 个 Swift 文件 → 3 条；191 个 TS 文件 → 8 条。加框架过滤之前，同一棵树报的是 60+ 和 9。

## 安装与使用

把整个文件夹放进你 Agent 的 skills 目录，或直接 clone 到那里：

```bash
git clone https://github.com/DreamOfXM/head-first-design-patterns \
  ~/.agents/skills/head-first-design-patterns
```

Qoder 读 `~/.agents/skills/`；其他消费 `SKILL.md` 形态 skill 的 Agent 用各自的目录（例如 `~/.claude/skills/`）。可以按名字调用，也可以让 description 自动路由——它的触发问法是"这里要不要用 X 模式""该用哪个模式""这个类为什么存在""这堆 if-else 怎么重构""我的抽象是不是过度设计""怎么让架构可扩展好测试""撤掉这层包装""写模式决策记录"。

闸门需要 `python3`；`javac`、`swiftc`、`node`/`tsc` 只有 `examples_check.py` 需要，缺了它报 `2` 而不是猜。

## 仓库结构

| 路径 | 内容 |
|---|---|
| [`SKILL.md`](SKILL.md) | 判定链条、触发表、最省阶梯、反查闸、两个闸门的退出码契约 |
| `references/*.md` | 15 个文件：每个模式的触发点、不该用的场景、更省替代、骨架、代价、证据 |
| `scripts/smell_scan.py` | 结构信号检波器 + 假阳/假阴夹具 |
| `scripts/examples_check.py` | 编译本仓库所有例子，三语齐跑 |
| `scripts/fixtures/` | 检波器夹具 — `java_decorator.java` 是夹具，不是模式例子 |
| [`CHANGELOG.md`](CHANGELOG.md) | 版本历史，1.0.0 → 1.3.0 |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | 改动检波器或例子前必须跑的两道闸门 |

## 溯源与授权

文字部分是**我对《Head First Design Patterns》（[第一版，O'Reilly 2004](https://www.oreilly.com/library/view/head-first-design/0596007124/)）中判断口径的改写**——没有逐字段落，没有复制图表，每条主张都给了页码区间以便你回书对照。本项目与原书作者和 O'Reilly 无隶属关系，也未获其背书，原书权利归其所有。

`scripts/` 下的代码与本仓库的骨架示例按 **[MIT](LICENSE)** 授权。要往里加内容请先看 [CONTRIBUTING.md 里的作者说明](CONTRIBUTING.md)。
