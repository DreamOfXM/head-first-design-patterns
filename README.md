# Design Pattern Judgment for Coding Agents

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Patterns](https://img.shields.io/badge/GoF%2023-covered-teal)](references/) [![Skeletons](https://img.shields.io/badge/examples%20compile-63%2F63-brightgreen)](scripts/examples_check.py)

**English** | [简体中文](README.zh-CN.md)

A [skill](SKILL.md) that makes an AI coding agent decide **whether a design pattern belongs in this code at all** — and if so, which one, at the cheapest rung that still solves it, at what cost, and how to take it back out. Distilled from *Head First Design Patterns* (1st ed., O'Reilly 2004); all 23 GoF patterns are covered.

The default answer is **"don't use a pattern"**, and the skill is built so that answer has to be written down and defended. Every "yes" must name the branch it deleted or the dependency edge it cut.

---

## What this is

Not a pattern catalog, not a tutorial, not a "use more patterns" scorecard. It is a judgment procedure the agent runs against your real files:

1. **Change sentence** — fill in `___ varies; ___ stays; ___ decides it, at ___ time`. No sentence, no pattern.
2. **Trigger table** — 24 rows of shapes you can actually see in code (type-switched construction, state-branched methods, wrapper constructors, per-handler boilerplate) → candidate pattern **and the cheaper alternative to try first**.
3. **Restraint ladder L0–L4** — literal → data (enum/transfer table/config) → injectable function → one injected object → pattern-shaped classes. Each promotion must answer: *which file did this turn read-only?*
4. **Eight-question back-check** — second implementation's file, change nameable or a "what if", layers added minus branches removed, real executor visible in the stack trace, object identity intact, who swaps it in tests, abstraction not leaking, and **how many consumer files removing this touches**.

Questions 1, 3 and 8 are counted with `grep`/`git diff`, not eyeballed; question 8 counts consumer files only, so 1 or 0 means the layer bought nothing. The commands are written out in [SKILL.md](SKILL.md).

Two more things are first-class: **[taking a pattern back out](SKILL.md)** (dead extension points, single-implementation interfaces, one-product factories) and a **[decision record template](SKILL.md)** you drop next to the code as `docs/adr/NNN-*.md`.

## What it deliberately does not cover

| Ask | Go instead |
|---|---|
| Reproduce a single bug | ordinary debugging |
| Does this screen look right | design/UI skills |
| How many services, what capacity, which DB | architecture-selection skills |
| Naming, formatting, local cleanup | code-style skills |
| Ship-blocking acceptance evidence | acceptance-testing skills |
| Verbatim text or diagrams from the book | the book itself |

## Coverage

| Where | Patterns | Depth |
|---|---|---|
| 11 chapter files in `references/` | Strategy, Observer, Decorator, Factory Method + Abstract Factory, Singleton, Command, Adapter + Facade, Template Method, Iterator + Composite, State, Proxy | Book chapters, with page ranges |
| [`compound-mvc.md`](references/compound-mvc.md) | MVC as a compound of three roles | Chapter 12 |
| [`leftover-patterns.md`](references/leftover-patterns.md) | Builder, Bridge, Chain of Responsibility, Flyweight, Interpreter, Mediator, Memento, Prototype, Visitor | **Catalog depth only** — the book devotes a lookup section to each; re-check against a dedicated source before you architect around one |
| [`restraint-and-workflow.md`](references/restraint-and-workflow.md) | Rule of Three, how to read a catalog entry, anti-pattern cards | Chapter 13 |
| [`disambiguation.md`](references/disambiguation.md) | Look-alike pairs, one deciding question each | Cross-chapter |

## Skeleton code

Every pattern position carries four blocks: **pseudocode roles → Java → Swift → TypeScript**. Java is the book's own language, rewritten as a minimal skeleton (not the book's listings); Swift and TypeScript are modern mappings and are labelled `（非本书）` where the shape differs.

All 63 blocks are compile-checked, per language column: `javac -d`, `swiftc -typecheck`, `tsc --noEmit --strict`. Scaffold types added purely so a block compiles standalone are marked `// ↓↓↓ 配套` and are not pattern content — take them with the skeleton or drop them, don't half-copy.

## Machine gates

```bash
python3 scripts/smell_scan.py <dir or files…>     # structural signals in YOUR code
python3 scripts/smell_scan.py --selftest          # the detectors still tell truth from fiction
python3 scripts/examples_check.py                 # do this skill's own examples still compile
python3 scripts/examples_check.py --selftest
```

Exit codes for both: `0` nothing found / everything compiles · `1` findings, or an example that no longer builds · `2` **this run cannot be judged** (bad path, unsupported files, toolchain missing or installed-but-unrunnable). `2` is never a pass and never a block — say "not judged".

Honest limits, stated in the skill itself:

- **The numeric thresholds are mine, not the book's.** The book contains no numeric criteria. A count decides only whether something is worth a human look.
- `smell_scan.py` is regex-level, not AST: macros, codegen, dynamic dispatch and multi-line conditions get missed, and the report says so.
- It filters framework and value types on purpose (`Button`, `URLSession`, `struct` construction, leading-dot modifier chains). Those exclusions are design decisions, not "already verified clean".
- Calibration on two real projects: 16 Swift files → 3 findings; 191 TS files → 8 findings. Before the framework filter, the same trees reported 60+ and 9.

## Install and use

Drop the folder into your agent's skills directory, or clone it there:

```bash
git clone https://github.com/DreamOfXM/head-first-design-patterns \
  ~/.agents/skills/head-first-design-patterns
```

Qoder reads `~/.agents/skills/`; other agents that consume `SKILL.md`-style skills use their own directory (e.g. `~/.claude/skills/`). Invoke it by name, or let the description route it — it triggers on questions like "should this use X here", "which pattern fits", "why does this class exist", "refactor this if-else pile", "is my abstraction over-engineered", "make this extensible and testable", "take this wrapper out", "write the pattern decision record".

Requires `python3` for the gates; `javac`, `swiftc`, `node`/`tsc` only for `examples_check.py`, which reports `2` without them rather than guessing.

## Repository layout

| Path | What it holds |
|---|---|
| [`SKILL.md`](SKILL.md) | The judgment chain, trigger table, restraint ladder, back-check gates, both gate contracts |
| `references/*.md` | 15 files: per-pattern triggers, don't-use cases, cheaper alternatives, skeletons, costs, evidence |
| `scripts/smell_scan.py` | Structural signal detector + fixtures for false positives and false negatives |
| `scripts/examples_check.py` | Compiles every shipped example, all three languages |
| `scripts/fixtures/` | Detector fixtures — `java_decorator.java` is a fixture, not a pattern example |
| [`CHANGELOG.md`](CHANGELOG.md) | Version history, 1.0.0 → 1.3.0 |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | The two gates you must run before changing detectors or examples |

## Provenance and license

The prose is **my rewrite of judgments** taken from *Head First Design Patterns* ([1st ed., O'Reilly 2004](https://www.oreilly.com/library/view/head-first-design/0596007124/)) — no verbatim passages, no reproduced figures, and page ranges are given for every claim so you can check it against the book. This project is not affiliated with or endorsed by the authors or O'Reilly; their rights are their own.

Code in `scripts/` and the skeleton examples in this repository are **[MIT](LICENSE)**. See [AUTHORS note in CONTRIBUTING.md](CONTRIBUTING.md) if you add to it.
