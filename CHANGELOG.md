# Changelog

All numbers below are re-counted by the scripts in `scripts/`, not carried over
from a previous release note.

The four versions were developed in one working session, so they record what
changed in which round — not four downloadable builds. This repository ships
from `main` and carries **no git tags and no GitHub Releases**: the install
paths (`git clone`, `npx skills add Owner/repo`) resolve the default branch and
pin by content hash in `skills-lock.json`, so nothing resolves a version string
here. The version truth is `_meta.json` plus this file. Cut a tag only when
something external starts resolving one.

## [1.3.0] — 2026-09-29

- Added a **Java** skeleton to every pattern position that already had Swift and
  TypeScript: 21 new blocks, so each of the 21 positions now carries
  pseudocode → Java → Swift → TypeScript (63 blocks, 63/63 compile).
- `examples_check.py` now validates three language columns instead of two
  (`javac -encoding UTF-8 -d`, `swiftc -typecheck`, `tsc --noEmit --strict`), and
  `--selftest` grew to one broken + one good block per language (6/6).
- **Fixed a gate that could invent defects.** Toolchain detection used to mean
  "the file exists". On macOS `/usr/bin/javac` is a forwarding shim that exits
  non-zero when no JDK is installed, so the previous check would have reported
  all 21 Java blocks as compile failures on a clean machine. Each tool is now
  probed by running `-version` / `--version`; an installed-but-unrunnable tool
  makes the whole language column `UNJUDGABLE` (exit `2`), which is reported as
  "not judged" rather than as a pass or as broken examples.
- `JAVAC=` / `SWIFTC=` / `TSC=` overrides are now strict (no silent fallback),
  and `tsc` discovery walks the current directory's ancestors and `$HOME`
  instead of pointing at one machine's path.
- SKILL.md's example and calibration claims rewritten for three languages, and
  page citations restated as book pages (the ebook's pagination runs ahead of the
  printed book).

## [1.2.0] — 2026-09-29

- Closed the gap where some pattern positions had prose but no code: all 23 GoF
  patterns now carry at least one compilable skeleton (14 covered by the 11
  chapter files, 9 by `leftover-patterns.md`).
- TypeScript blocks are compiled with `--strict` against a real `tsc`; the Swift
  column no longer depends on top-level statements being legal, which `swiftc`
  rejects outside `main.swift`.

## [1.1.0] — 2026-09-29

- `smell_scan.py`: the no-op-override detector missed the single-line form
  (`override func foo() {}`) — it now catches both shapes, with a fixture for
  the line that used to slip through.
- Removed `/tmp` paths and unattributable line numbers from evidence lines in
  `references/*`, which had made the doc point at files that no longer exist.
- Eight judgment gaps in SKILL.md fixed (evidence tiers for "nameable change",
  the consumer-only counting rule for back-check question 8, the decorator
  composition test for taking a pattern back out, merged exit-code contract).
- `_meta.json` added as a byte-identical mirror of the frontmatter: single-line
  `description` and its 8 trigger phrases. The frontmatter remains the only
  trigger source of truth.

## [1.0.0] — 2026-09-29

Initial distillation of *Head First Design Patterns* (1st ed.) into a judgment
procedure rather than a catalog: change sentence → 24-row trigger table →
restraint ladder L0–L4 → eight-question back-check → when to take a pattern back
out → decision record template. 15 reference files (11 chapter files,
`leftover-patterns.md` for the 9 appendix-only patterns, `compound-mvc.md`,
`restraint-and-workflow.md`, `disambiguation.md`), plus `smell_scan.py`
(structural signals with false-positive/false-negative fixtures) and
`examples_check.py` (compiles the shipped examples).
