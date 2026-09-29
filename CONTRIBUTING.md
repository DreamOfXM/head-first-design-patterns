# Contributing

## What this repo is

A **judgment procedure**, not a pattern catalog. The value is in the ordering —
change sentence → trigger table → restraint ladder → back-check — and in the
parts that say *don't use a pattern*. A PR that adds a pattern write-up without
also giving its trigger-table row, its cheaper alternative, and its back-check
question is incomplete by design.

## The gates you must run

```bash
python3 scripts/smell_scan.py --selftest       # detectors still tell truth from fiction
python3 scripts/examples_check.py              # every shipped example still compiles
python3 scripts/examples_check.py --selftest   # the compile gate isn't asleep
```

If you changed a detector, also run `smell_scan.py` against real code and add a
fixture under `scripts/fixtures/` for the case you fixed — both the false-positive
and the false-negative kind. A detector change without a fixture is how
`noop_override` lost its single-line form once already.

Exit codes for both scripts: `0` clean · `1` findings, or an example that no
longer builds · `2` this run cannot be judged. **Never read `2` as a pass, and
never report a missing or unrunnable toolchain as broken examples.** Absent
compiler means "not judged for that language column".

## Example conventions

- Each pattern position carries four blocks in this order: pseudocode roles →
  Java → Swift → TypeScript. Java is the book's language; Swift and TS are modern
  mappings and get labelled `（非本书）` where the shape differs.
- A block must compile standalone. Scaffold types added only to make it compile
  sit under a `// ↓↓↓ 配套` marker so readers know they aren't pattern content.
- Fences are ```java / ```swift / ```ts and are found by regex. An unknown
  language tag makes `examples_check.py` exit `2` on purpose — don't invent tags.

## Provenance rules

- No verbatim passages, figures, or listings from *Head First Design Patterns*.
  Rewrite the judgment, and cite the **printed page** range so it can be checked
  (the ebook's pagination runs ahead of the printed book).
- Anything not from the book — numeric thresholds, modern-language substitutes,
  tooling opinions — must be marked as the author's own, the way the scan
  thresholds already are.
- Keep README's non-affiliation statement accurate if the scope grows.

## Metadata and README sync

- `SKILL.md` frontmatter `description` is the only trigger source of truth: one
  line, ≤1024 chars. `_meta.json` stays byte-identical to it, and its
  `trigger_words` mirror the phrases inside it. Bump `_meta.json`'s `version` in
  the same commit and add a `CHANGELOG.md` entry with re-counted numbers.
- Body stays under 500 lines; split into `references/` rather than growing it.
- README changes come in pairs, and the parity gate compares structure (sections,
  bullets, tables, rows, fences, badges, external-link set, local paths) rather
  than wording:

```bash
python3 ~/.agents/skills/github-readme-best-practices/scripts/readme-parity.py \
  README.md README.zh-CN.md
```

## Authors note

This is a personal project by **DreamOfXM**. Contributions are licensed under
the MIT license in `LICENSE` — the code *and* your prose, since text here is a
distillation and needs the same clearance as the scripts. By opening a PR you
confirm that you wrote it, that it copies nothing verbatim from the book, and
that you have the right to offer it under MIT.

Please keep machine-specific paths out of the files: no home directories, no
personal project names, no local evidence paths. Evidence for a claim belongs in
a commit message or PR comment, not in the shipped markdown.
