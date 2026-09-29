#!/usr/bin/env python3
"""Compile-check every code example shipped in references/*.md.

Purpose: the skill promises each of the 23 GoF patterns carries a minimal
skeleton in Java, Swift and TypeScript. This turns that promise into a
machine-checked fact: a skeleton that does not compile is a broken example, not
a teaching aid.

Usage:
  python3 examples_check.py [--dir references] [--langs java,swift,ts] [--quiet]

Exit codes:
  0  every extracted block compiles
  1  at least one block fails to compile
  2  cannot judge (toolchain missing, references dir missing, no blocks found)

stdout is meant to be read directly by an agent: one line per block, then a
summary. Compiler output is truncated to the first few distinct errors.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

MAX_LANGS = ("java", "swift", "ts")
EXT = {"java": "java", "swift": "swift", "ts": "ts"}
NODE = shutil.which("node") or "node"
FENCE = re.compile(r"^```([a-zA-Z0-9]+)[ \t]*\n(.*?)^```", re.S | re.M)
TSC_REL = (os.path.join("node_modules", ".bin", "tsc"),
           os.path.join("node_modules", "typescript", "bin", "tsc"))
JAVAC_CANDIDATES = [
    "/usr/bin/javac",
    "/opt/homebrew/opt/openjdk@17/bin/javac",
    "/usr/local/opt/openjdk@17/bin/javac",
]


def _child_dirs(path, limit=300):
    try:
        return sorted(e.name for e in os.scandir(path)
                      if e.is_dir(follow_symlinks=False) and not e.name.startswith("."))[:limit]
    except OSError:
        return []


def find_swiftc():
    if os.environ.get("SWIFTC"):
        cand = os.environ["SWIFTC"]
        return cand if os.path.exists(cand) and probe(cand) else None
    for cand in (shutil.which("swiftc"), "/usr/bin/swiftc"):
        if cand and os.path.exists(cand) and probe(cand):
            return cand
    return None


def find_javac():
    # JAVAC= is an explicit override: if it is set and unusable, that is UNJUDGABLE, not "silently try others".
    if os.environ.get("JAVAC"):
        cand = os.environ["JAVAC"]
        return cand if os.path.exists(cand) and probe(cand) else None
    # /usr/bin/javac on macOS is a shim that exits non-zero when no JDK is installed,
    # so "the file exists" is not enough — a tool that cannot run means the whole
    # language column is UNJUDGABLE, and reporting its blocks as compile failures
    # would be the gate inventing 21 broken examples.
    for cand in [shutil.which("javac")] + JAVAC_CANDIDATES:
        if cand and os.path.exists(cand) and probe(cand):
            return cand
    return None


def find_tsc():
    if os.environ.get("TSC"):
        cand = os.environ["TSC"]
        return cand if os.path.exists(cand) and probe_tsc(cand) else None
    found = shutil.which("tsc")
    if found and probe_tsc(found):
        return found
    # No typescript install is on PATH on most machines, so look for one instead of
    # hardcoding a particular machine's path: ancestors of the cwd, then two levels
    # under $HOME. Nothing found -> UNJUDGABLE, not "the TS examples are broken".
    roots, d = [], os.path.abspath(os.getcwd())
    while True:
        roots.append(d)
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    home = os.path.expanduser("~")
    roots.append(home)
    for a in _child_dirs(home):
        roots.append(os.path.join(home, a))
        for b in _child_dirs(os.path.join(home, a)):
            roots.append(os.path.join(home, a, b))
    for root in roots:
        for rel in TSC_REL:
            cand = os.path.join(root, rel)
            if os.path.exists(cand) and probe_tsc(cand):
                return cand
    return None


SELFTEST = [("swift", "struct A { func f() { notAThing() } }\n", False),
            ("swift", "struct A { func f() { print(1) } }\n", True),
            ("ts", "const a: number = 'x';\nexport { a };\n", False),
            ("ts", "export const a: number = 1;\n", True),
            ("java", "class Bad { void f() { notAThing(); } }\n", False),
            ("java", "class Good { void f() { System.out.println(1); } }\n", True)]


def run(cmd, cwd=None):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=180)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 99, str(exc)


def probe(binary):
    """Does this compiler actually run? Existence is not enough (macOS javac shim)."""
    code, _ = run([binary, "-version"])
    return code == 0


def probe_tsc(tsc):
    """tsc is a JS file, so it only runs through node — and node missing would make
    every TS block look broken, which is why the node check belongs to toolchain discovery."""
    if not shutil.which("node"):
        return False
    code, _ = run([NODE, tsc, "--version"])
    return code == 0


def compile_swift(swiftc, path):
    code, out = run([swiftc, "-typecheck", path])
    return code, out


def compile_ts(tsc, path):
    code, out = run([NODE, tsc, "--noEmit", "--strict", "--target", "es2022",
                     "--lib", "es2022,dom", "--skipLibCheck", path])
    return code, out


def compile_java(javac, path, outdir):
    code, out = run([javac, "-encoding", "UTF-8", "-nowarn", "-d", outdir, path])
    return code, out


def compile_for(tools, work):
    """Return compile(lang, path) -> (exit_code, output) for the languages requested."""
    javac, swiftc, tsc = tools.get("java"), tools.get("swift"), tools.get("ts")
    jout = os.path.join(work, "javac-out")

    def comp(lang, path):
        if lang == "java":
            os.makedirs(jout, exist_ok=True)
            return compile_java(javac, path, jout)
        if lang == "swift":
            return compile_swift(swiftc, path)
        return compile_ts(tsc, path)

    return comp


def summarize(out, limit=3):
    errs = []
    for ln in out.splitlines():
        m = (re.search(r"error: (.*?)\s*$", ln) or re.search(r"(error TS\d+: .*?)\s*$", ln)
             or re.search(r"错误: (.*?)\s*$", ln))
        if m:
            msg = m.group(1)
            if msg not in errs:
                errs.append(msg)
    if not errs:
        return (out.strip().splitlines() or ["(no output)"])[:limit][0]
    tail = f" (+{len(errs) - limit} more)" if len(errs) > limit else ""
    return "; ".join(errs[:limit]) + tail


def main():
    ap = argparse.ArgumentParser(description="compile-check the skill's pattern examples")
    ap.add_argument("--dir", default=None, help="references dir (default: ../references)")
    ap.add_argument("--langs", default=",".join(MAX_LANGS), help="comma list: java,swift,ts")
    ap.add_argument("--quiet", action="store_true", help="only failures and the summary")
    ap.add_argument("--selftest", action="store_true",
                    help="prove the gate distinguishes a broken example from a good one")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    refs = args.dir or os.path.join(os.path.dirname(here), "references")
    if not os.path.isdir(refs):
        print(f"UNJUDGABLE: references dir not found: {refs}")
        return 2

    langs = [l.strip() for l in args.langs.split(",") if l.strip()]
    unknown = [l for l in langs if l not in MAX_LANGS]
    if unknown:
        print(f"UNJUDGABLE: 不认识的语言 {unknown}（可选：{','.join(MAX_LANGS)}）")
        return 2
    tools = {"java": find_javac() if "java" in langs else None,
             "swift": find_swiftc() if "swift" in langs else None,
             "ts": find_tsc() if "ts" in langs else None}
    missing = []
    if "java" in langs and not tools["java"]:
        missing.append("javac (JDK 未装或 /usr/bin/javac 只是转发自检失败；设 JAVAC=/path/to/javac)")
    if "swift" in langs and not tools["swift"]:
        missing.append("swiftc (Xcode/CommandLineTools)")
    if "ts" in langs and not tools["ts"]:
        missing.append("tsc (set TSC=/path/to/tsc)")
    if "ts" in langs and not shutil.which("node"):
        missing.append("node (tsc 需要它；缺了会把 TS 例子全误判成编译失败)")
    if missing:
        print("UNJUDGABLE: toolchain missing -> " + ", ".join(missing))
        print("按报告纪律写「未判读」，不得算通过、也不得算拦下。")
        return 2
    if not args.quiet:
        print("toolchain: " + " ".join(f"{l}={tools[l] or '-'}" for l in MAX_LANGS if l in langs)
              + f" node={shutil.which('node')}")

    blocks = []
    per_file = {}
    for name in sorted(os.listdir(refs)):
        if not name.endswith(".md"):
            continue
        text = open(os.path.join(refs, name), encoding="utf-8").read()
        for m in FENCE.finditer(text):
            lang = m.group(1).lower()
            if lang not in langs:
                continue
            head = re.findall(r"^##[ \t]+(.*?)[ \t]*$", text[:m.start()], re.M)
            where = head[-1].strip() if head else "(top)"
            blocks.append((name, lang, m.group(2), where))
            per_file.setdefault(name, {}).setdefault(lang, 0)
            per_file[name][lang] += 1

    if not blocks:
        print(f"UNJUDGABLE: no ```java / ```swift / ```ts block found under {refs}")
        return 2

    work = tempfile.mkdtemp(prefix="hfdp-examples-")
    compile = compile_for(tools, work)
    failed = 0
    try:
        if args.selftest:
            bad = 0
            for lang, snippet, expect_ok in SELFTEST:
                path = os.path.join(work, f"selftest.{EXT[lang]}")
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(snippet)
                code, out = compile(lang, path)
                got_ok = code == 0
                verdict = "ok" if got_ok == expect_ok else "SELFTEST-FAIL"
                if verdict != "ok":
                    bad += 1
                print(f"{verdict}  selftest/{lang} expect={'ok' if expect_ok else 'fail'} got={code}")
            shutil.rmtree(work, ignore_errors=True)
            if bad:
                print("RESULT: 闸门自检不通过——它区分不出坏例子，上面的通过/失败都不可信")
                return 1
            print(f"RESULT: selftest {len(SELFTEST)}/{len(SELFTEST)} — 闸门能判真伪")
            return 0

        for idx, (src, lang, body, where) in enumerate(blocks):
            stem = os.path.splitext(src)[0]
            suffix = f"  <- {where}" if per_file[src][lang] > 1 else ""
            path = os.path.join(work, f"{idx:02d}_{stem}.{EXT[lang]}")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(body)
            code, out = compile(lang, path)
            label = f"{stem}.{EXT[lang]}{suffix}"
            if code == 0:
                if not args.quiet:
                    print(f"ok    {label}")
            else:
                failed += 1
                print(f"FAIL  {label}  [{code}]  {summarize(out)}")
    finally:
        shutil.rmtree(work, ignore_errors=True)

    per_lang = {l: sum(v.get(l, 0) for v in per_file.values()) for l in MAX_LANGS}
    files_n = len(per_file)
    counts = ", ".join(f"{l} {per_lang[l]}" for l in MAX_LANGS if per_lang[l])
    print(f"\ncoverage: {files_n} file(s) carry examples — {counts}, total {len(blocks)}")
    for name in sorted(per_file):
        if not args.quiet:
            counts = ", ".join(f"{k}={v}" for k, v in sorted(per_file[name].items()))
            print(f"  {name}: {counts}")
    total = len(blocks)
    if failed:
        print(f"RESULT: {failed}/{total} block(s) do not compile — 示例已失效，不得引用")
        return 1
    print(f"RESULT: {total}/{total} block(s) compile")
    return 0


if __name__ == "__main__":
    sys.exit(main())
