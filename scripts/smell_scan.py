#!/usr/bin/env python3
"""smell_scan.py — 结构信号扫描器（head-first-design-patterns 的机器闸门）。

只报"代码里看得见的结构形状"，不判该不该上模式；判读由调用方逐条完成。
纯正则（非 AST）：宏、代码生成、动态派发、复杂泛型推导会漏。退出码 0/1/2 见 main。
"""
import os
import re
import sys

VERSION = "1"
MAX_BYTES = 1_500_000
SKIP_DIRS = {".git", "node_modules", "build", "dist", "DerivedData", ".build", "Pods",
             "venv", ".venv", "__pycache__", "target", "out", ".next", "Carthage", "vendor"}

LANG_BY_EXT = {
    ".swift": "swift", ".ts": "ts", ".tsx": "ts", ".js": "js", ".jsx": "js",
    ".mjs": "js", ".cjs": "js", ".py": "py", ".java": "java", ".kt": "kt",
}

# 阈值是我拍的初值（原书没有任何数值判据）。它们只决定"值不值得看一眼"，
# 不得被表述成"超过 N 就该上模式"。
THRESHOLDS = [
    ("tag_switch 分支臂", 3), ("分支臂间隔行", 8), ("状态分支同文件处数", 2),
    ("同一具体类型被构造的文件数", 2), ("继承链深度", 3), ("手写监听器定义数", 3),
    ("纯转发方法数", 4), ("链式取值跳数", 3), ("同一前置动作重复处数", 3),
    ("抽象的实现点数", 1),
]

SWIFT_BUILTIN_CALLS = {
    "Array", "Dictionary", "Set", "Data", "URL", "Date", "URLComponents", "CGPoint",
    "CGRect", "CGSize", "UIColor", "NSColor", "String", "Int", "Double", "Float",
    "Optional", "Task", "Result", "AnyView", "Text", "VStack", "HStack", "List",
    "Image", "Path", "Color", "FileManager", "JSONDecoder", "JSONEncoder", "UUID",
    "Notification", "URLRequest", "URLSession", "OperationQueue", "DispatchQueue",
    "Timer", "Grouping", "Tuple", "Some", "Any",
}

DISCRIMINATOR = re.compile(
    r"\b(kind|type|tag|mode|status|state|phase|role|flavor|category|operator|op|action|"
    r"event|format|source|channel|provider|vendor|platform|tier|level)s?\b", re.I)

FUNC_HEAD = re.compile(
    r"^\s{0,8}(?:@\w+\s+)?(?:(?:public|private|protected|internal|open|static|final|override|"
    r"async|mutating|virtual|abstract|suspend|func|fun|def|function)\s+)*"
    r"(?:func|fun|def|function)?\s*[A-Za-z_]\w*\s*\([^)]*\)\s*(?:->[^{:]+|:[^{]+|throws|async)?\s*\{?\s*[:;]?\s*$")


class Sig:
    __slots__ = ("name", "path", "line", "detail", "excerpt", "cands")

    def __init__(self, name, path, line, detail, excerpt, cands):
        self.name, self.path, self.line = name, path, line
        self.detail, self.excerpt, self.cands = detail, excerpt or "", cands

    def __str__(self):
        loc = "%s:%d" % (self.path, self.line) if self.line else self.path
        return "[%s] %s · %s\n      候选→ %s\n      > %s" % (
            self.name, self.detail, loc, self.cands, self.excerpt.strip()[:100])


def strip_comments(text, lang):
    text = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    out = []
    for ln in text.split("\n"):
        if lang == "py":
            out.append(re.sub(r"\s#.*$", "", ln) if not ln.strip().startswith("#") else "")
        else:
            out.append(re.sub(r"(?<!:)//.*$", "", ln))
    return out


def read_files(paths):
    files, skipped = [], []
    for root in paths:
        if os.path.isfile(root):
            cands = [root]
        elif os.path.isdir(root):
            cands = []
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
                cands += [os.path.join(dirpath, f) for f in filenames]
            cands.sort()
        else:
            skipped.append((root, "路径不存在"))
            continue
        for p in cands:
            lang = LANG_BY_EXT.get(os.path.splitext(p)[1].lower())
            if not lang:
                continue
            try:
                if os.path.getsize(p) > MAX_BYTES:
                    skipped.append((p, "超大已跳过"))
                    continue
                raw = open(p, encoding="utf-8", errors="replace").read()
            except OSError as e:
                skipped.append((p, "读不了:%s" % (e.strerror or "?")))
                continue
            files.append((p, lang, strip_comments(raw, lang)))
    return files, skipped


# ---------------- 单文件 ----------------

def det_tag_switch(path, lang, lines):
    arm = re.compile(r"^\s*(?:case|when)\s+(.+?)\s*:\s*$")
    elifarm = re.compile(r"^\s*elif\s+(.+?):\s*$")
    head = re.compile(r"\b(switch|match|select|case)\s*[({\w]")
    arms = []
    for i, ln in enumerate(lines):
        m = arm.match(ln) or (elifarm.match(ln) if lang == "py" else None)
        if m:
            arms.append((i, m.group(1) if hasattr(m, "group") else ""))
    groups, cur = [], []
    for i, key in arms:
        if cur and i - cur[-1][0] > THRESHOLDS[1][1]:
            groups.append(cur)
            cur = []
        cur.append((i, key))
    if cur:
        groups.append(cur)
    out = []
    for g in groups:
        if len(g) < THRESHOLDS[0][1]:
            continue
        above = "\n".join(lines[max(0, g[0][0] - 14):g[0][0] + 1])
        keys = " ".join(k for _, k in g)
        d = DISCRIMINATOR.search(above) or DISCRIMINATOR.search(keys)
        if not d and not head.search(above):
            continue
        out.append(Sig("tag_switch", path, g[0][0] + 1,
                       "%d 个分支臂，判据词 %s" % (len(g), d.group(0) if d else "switch/case"),
                       lines[g[0][0]],
                       "Strategy(第1章) / 工厂(第4章) / State(第10章) / Command 表(第6章)"))
    return out


def det_state_branch(path, lang, lines):
    # 只算"控制流里按状态字段分支"。`state: state,`（初始化标签）和
    # `filter { $0.state == .working }`（数据筛选）都不是 State 的候选，是噪声。
    branch_kw = re.compile(r"\b(if|else\s+if|guard|while|switch|case)\b|\?\s*[\w.]", re.I)
    field = re.compile(r"(?:[.\w]\s*)?\b(state|status|mode|phase|step)s?\s*(?:==|!=|===)")
    dotted = re.compile(r"\.\s*(state|status|mode|phase|step)\b")
    hits = []
    for i, ln in enumerate(lines):
        if not branch_kw.search(ln):
            continue
        if field.search(ln) or (dotted.search(ln) and re.search(r"\b(switch|if|guard|while)\b", ln, re.I)):
            hits.append((i + 1, ln))
    if len(hits) < THRESHOLDS[2][1]:
        return []
    n0, ln0 = hits[0]
    return [Sig("state_field_branch", path, n0,
                "按状态字段分支（本文件 %d 处：行 %s）"
                % (len(hits), ",".join(str(n) for n, _ in hits[:12])), ln0,
                "State(第10章)；先试 enum/判别联合 + 一张转移表")]


def construction_sites(path, lang, lines):
    out = []
    npat = re.compile(r"\bnew\s+([A-Z]\w*)\s*\(")
    spat = re.compile(r"(?:=|\(|,|:|\s)\s*([A-Z]\w*)\s*\(")
    for i, ln in enumerate(lines):
        for m in npat.finditer(ln):
            out.append((i + 1, m.group(1), ln))
        if lang == "swift":
            for m in spat.finditer(ln):
                if m.group(1) not in SWIFT_BUILTIN_CALLS:
                    out.append((i + 1, m.group(1), ln))
    return out


def det_wrapper_chain(path, lang, lines):
    pat = re.compile(r"\bnew\s+([A-Z]\w*)\s*\(\s*new\s+([A-Z]\w*)")
    spat = re.compile(r"=\s*([A-Z]\w*)\(\s*([A-Z]\w*)\(")
    # 装饰/包装栈经常跨行写（一层一行），单行正则看不见，会给出假的"无信号"。
    starts = [i for i, ln in enumerate(lines)
              if re.search(r"\bnew\s+[A-Z]\w*\s*\(|=\s*[A-Z]\w*\s*\(", ln)]
    out, claimed = [], set()
    for i in starts:
        if i in claimed:
            continue
        for w in (1, 3, 5, 7, 9):
            blob = " ".join(x.strip() for x in lines[i:i + w])
            if pat.search(blob) or (lang == "swift" and spat.search(blob)):
                claimed.update(range(i, min(i + w, len(lines))))
                out.append(Sig("wrapper_chain", path, i + 1,
                               "构造时嵌套包装（跨 %d 行）" % w, lines[i],
                               "Decorator(第3章) 或 Proxy(第11章)；链长>3 要查身份/相等性/可调试性"))
                break
    return out


def det_global_access(path, lang, lines):
    # 系统/框架自带的单例访问点不是我们的设计选择，报出来只会淹掉真信号。
    system_recv = re.compile(r"^(?:NS|UI|CG|CA|SK)\w+$|^URLSession$|^FileManager$|^ProcessInfo$"
                             r"|^UserDefaults$|^Configuration$")
    pats = [(re.compile(r"\b([\w.]+)\.shared\b"), "静态访问点 .shared", "recv"),
            (re.compile(r"\b([\w.]+)\.getInstance\s*\("), "getInstance() 访问点", "recv"),
            (re.compile(r"^export\s+(?:const|let)\s+\w+\s*=\s*new\s+\w+"), "模块级实例导出", None),
            (re.compile(r"^[a-z_]\w*\s*=\s*[A-Z]\w*\(.*\)\s*$"), "模块级实例", None)]
    buckets, order = {}, []
    for i, ln in enumerate(lines):
        for p, label, kind in pats:
            m = p.search(ln)
            if not m:
                continue
            if kind == "recv" and system_recv.match(m.group(1).split(".")[-1]):
                continue
            if label not in buckets:
                buckets[label] = []
                order.append(label)
            buckets[label].append((i + 1, ln))
    out = []
    for label in order:
        hits = buckets[label]
        n0, ln0 = hits[0]
        out.append(Sig("global_access_point", path, n0,
                       "%s（本文件 %d 处：行 %s）"
                       % (label, len(hits), ",".join(str(n) for n, _ in hits[:12])), ln0,
                       "Singleton(第5章)；先问'构造参数注入'够不够"))
    return out


EMPTY_BODY = re.compile(r"^\s*(?:\}|pass\b|return\s*(?:nil|None|null|\[\]|\(\)|0|false|False)\s*;?|"
                        r"(?://|#)\s*(?:TODO|FIXME|no-?op)\b.*)$")

# 同行写法：`override func cost() -> Int { }`、`class Cat: A { override f() {} }`。
# FUNC_HEAD 要求声明独占一行，所以整行写完的空覆盖此前看不见（Swift/TS/Java 同形）。
# 注释在进检测器前已被 strip_comments 抹掉，故这里不再列注释分支。
INLINE_NOOP = re.compile(
    r"\b@?[Oo]verride\b[^{};]*\([^()]*\)[^{};]*\{\s*"
    r"(?:\}|pass\b|return\s*(?:nil|None|null|\[\]|\(\)|0|false|False|\"\"|'')\s*;?)\s*\}")


def det_noop_override(path, lang, lines):
    out = []
    for i, ln in enumerate(lines):
        if not re.search(r"\b@?[Oo]verride\b", ln):
            continue
        if INLINE_NOOP.search(ln):
            out.append(Sig("noop_override", path, i + 1, "覆盖后什么都不做（第 1 章的继承味道）", ln,
                           "优先组合(第1章) / Strategy / 把这一步做成可选钩子或拆模板"))
            continue
        if not FUNC_HEAD.match(ln):
            continue
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines) and EMPTY_BODY.match(lines[j]):
            out.append(Sig("noop_override", path, i + 1, "覆盖后什么都不做（第 1 章的继承味道）", ln,
                           "优先组合(第1章) / Strategy / 把这一步做成可选钩子或拆模板"))
    return out


def det_listener_plumbing(path, lang, lines):
    # 三个角色：注册 / 注销 / 派发。只认 addListener 系会漏掉现代写法 on/off/emit、
    # subscribe/unsubscribe/publish，而那些恰恰是最常见的手写 Observer。
    roles = {
        "register": r"on|add[_-]?(?:\w*[_-])?(?:listener|observer|subscriber)|register(?!ed)|subscribe|observe",
        "unregister": r"off|remove[_-]?(?:\w*[_-])?(?:listener|observer|subscriber)|unregister|unsubscribe",
        "dispatch": r"emit|notify|dispatch|fire|trigger|broadcast|publish",
    }
    head = (r"^\s*(?:@\w+\s+)?(?:(?:public|private|protected|internal|open|static|final|export|"
            r"async|override|func|fun|def|void)\s+)*")
    tail = r"\s*\([^)]*\)\s*(?:->[^{:]+|:[^{]*)?\s*[{:]\s*$"
    found = {}
    for i, ln in enumerate(lines):
        for role, names in roles.items():
            if re.match(head + r"(?:%s)%s" % (names, tail), ln, re.I):
                found.setdefault(role, []).append((i + 1, ln))
    hit_roles = [r for r in roles if found.get(r)]
    total = sum(len(v) for v in found.values())
    if len(hit_roles) < 2 or total < THRESHOLDS[4][1]:
        return []
    allhits = sorted([(n, l) for r in hit_roles for n, l in found[r]])
    first, ln0 = allhits[0]
    return [Sig("handrolled_observer_machinery", path, first,
                "手写监听器机制：角色 %s，共 %d 个定义（行 %s）"
                % ("/".join(hit_roles), total,
                   ",".join(str(n) for r in hit_roles for n, _ in found[r][:12])), ln0,
                "框架多半已有此形状(第12章)：NotificationCenter/Combine/EventEmitter/EventTarget/RxJS")]


def next_nonblank(lines, i):
    while i < len(lines) and not lines[i].strip():
        i += 1
    return i


def det_passthrough(path, lang, lines):
    body = re.compile(r"^\s+(?:return\s+)?(?:this|self)\.(\w+)\.(\w+)\s*\(")
    count, first = 0, None
    for i, ln in enumerate(lines):
        if not FUNC_HEAD.match(ln) or not re.search(r"\(.*\)", ln):
            continue
        j = next_nonblank(lines, i + 1)
        if j >= len(lines) or not body.match(lines[j]):
            continue
        k = next_nonblank(lines, j + 1)
        ends = k >= len(lines) or re.match(r"^\s*[\}\)]", lines[k]) or \
            (lang == "py" and (FUNC_HEAD.match(lines[k]) or lines[k].strip() == ""))
        if ends:
            count += 1
            first = first or (i + 1, ln)
    if count >= THRESHOLDS[6][1] and first:
        return [Sig("passthrough_class", path, first[0],
                    "%d 个方法只做一次转发" % count, first[1],
                    "Facade(第7章)；原书反对'给每个子系统都套一个壳'")]
    return []


def det_train_wreck(path, lang, lines):
    pat = re.compile(r"(\.\w+\([^)]*\)){%d,}" % THRESHOLDS[7][1])
    out = []
    for i, ln in enumerate(lines):
        # 行首的点是同一对象上的流式构造（SwiftUI 修饰符 / lodash 链），不是跨对象取值。
        if ln.lstrip().startswith("."):
            continue
        if pat.search(ln):
            out.append(Sig("chained_getters", path, i + 1, "跨多层取值", ln,
                           "第 7 章最少知识：在归属类型上给一个转发方法，或让中间类型变成值"))
    return out


CROSS_KW = re.compile(r"\b(log|logger|track|audit|metric|metrics|timer|signpost|verify|check|"
                      r"guard|require|authorize|permission|assert|telemetry)\w*", re.I)


def det_cross_cutting(path, lang, lines):
    buckets, order = {}, []
    for i, ln in enumerate(lines):
        if not FUNC_HEAD.match(ln) or not re.search(r"\(.*\)", ln):
            continue
        j = next_nonblank(lines, i + 1)
        if j >= len(lines):
            continue
        body = lines[j].strip().rstrip(";{")
        if len(body) > 90 or not body or not CROSS_KW.search(body):
            continue
        key = re.sub(r"[A-Za-z_]\w*\s*\(", "(", body)[:70]
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(i + 1)
    out = []
    for key in order:
        locs = buckets[key]
        if len(locs) >= THRESHOLDS[8][1]:
            out.append(Sig("cross_cutting_repeat", path, locs[0],
                           "同一前置动作重复 %d 处（行 %s）" % (len(locs), ",".join(map(str, locs[:10]))),
                           lines[locs[0] - 1],
                           "横切关注点：中间件/拦截器/装饰型代理(第11章)；别每个 handler 各写一遍"))
    return out


CLASS_PARENT = re.compile(
    r"^\s*(?:final\s+|open\s+|abstract\s+|sealed\s+|public\s+|private\s+|internal\s+)*"
    r"(?:class|struct|enum|actor)\s+([A-Z]\w*)[^:{=]*?(?::|extends|implements|\b)\s*([A-Z]\w*)")


def inheritance_edges(lines, path):
    out = []
    for i, ln in enumerate(lines):
        m = re.match(r"^\s*(?:final\s+|open\s+|abstract\s+|sealed\s+|public\s+|private\s+)*"
                     r"(?:class|struct|actor)\s+([A-Z]\w*)\s*(?:<[^>]*>)?\s*"
                     r"(?::|extends|implements)\s*([A-Z]\w*)", ln)
        if m and m.group(2) not in ("Protocol", "NSObject", "AnyObject"):
            out.append((m.group(1), m.group(2), i + 1, ln))
        elif m:
            continue
        mp = re.match(r"^\s*class\s+([A-Z]\w*)\(([^)]*)\)\s*:", ln)  # python
        if mp:
            base = re.search(r"[A-Z]\w*", mp.group(2))
            if base and base.group(0) not in ("object", "Exception", "BaseException"):
                out.append((mp.group(1), base.group(0), i + 1, ln))
    return out


IFACE_DECL = re.compile(r"^\s*(?:public |open |internal |private |export )*?"
                        r"(?:interface|protocol)\s+([A-Z]\w*)|^\s*(?:public |abstract )*?abstract class\s+([A-Z]\w*)")
IFACE_USE = re.compile(r"(?::|extends|implements)\s*([A-Z]\w*(?:\s*,\s*[A-Z]\w*)*(?:\s*<[^>]*>)?)")


CONCRETE_DECL = re.compile(r"^\s*(?:@\w+\s+)?(?:(?:public|private|internal|open|final|abstract|"
                           r"sealed|export|declare|data|inner|companion)\s+)*"
                           r"(?:class|struct|enum|actor|object|extension)\s+[A-Z]\w*")


def seam_edges(lines, path):
    decls, impls = set(), []
    for i, ln in enumerate(lines):
        m = IFACE_DECL.match(ln)
        if m:
            decls.add(m.group(1) or m.group(2))
        # 实现点必须是具体类型声明。`interface X extends Y` 是类型继承，不算一处实现，
        # 否则 TS 的类型分层会被误报成"抽象只有一个实现"。
        if not CONCRETE_DECL.match(ln):
            continue
        for mm in IFACE_USE.finditer(ln):
            for name in re.split(r"\s*,\s*", mm.group(1).split("<")[0]):
                if re.match(r"^[A-Z]\w*$", name):
                    impls.append((name, path, i + 1, ln))
    return decls, impls


# ---------------- 跨文件 ----------------

REF_DECL = re.compile(r"^\s*(?:(?:final|open|abstract|sealed|public|private|internal|protected|"
                      r"export|declare|data|async)\s+)*(?:class|actor)\s+([A-Z]\w*)")


def det_spread(files):
    # 只报"本项目里声明过的引用类型"。框架类型（Button/NSImage/DateFormatter）和
    # 值类型（struct/enum，多半是 DTO）的多点构造是正常数据管线，第 4 章也反对给 DTO 造工厂。
    declared = set()
    for _, _, lines in files:
        for ln in lines:
            m = REF_DECL.match(ln)
            if m:
                declared.add(m.group(1))
    sites = {}
    for path, lang, lines in files:
        for line_no, typ, ln in construction_sites(path, lang, lines):
            if typ in declared:
                sites.setdefault(typ, []).append((path, line_no, ln))
    out = []
    for typ, locs in sorted(sites.items()):
        if len({p for p, _, _ in locs}) >= THRESHOLDS[3][1]:
            p, n, ln = locs[0]
            out.append(Sig("concrete_type_spread", p, n,
                           "具体类型 %s 在 %d 个文件里被构造（共 %d 处）"
                           % (typ, len({p for p, _, _ in locs}), len(locs)), ln,
                           "工厂 + 组合根(第4章：每个 new 都是一条依赖边)"))
    return out


def det_deep_inheritance(files):
    parent, where = {}, {}
    for path, lang, lines in files:
        for child, par, n, ln in inheritance_edges(lines, path):
            if child not in parent:
                parent[child], where[child] = par, (path, n, ln)
    out, seen = [], set()
    for child in parent:
        chain, cur = [child], child
        for _ in range(12):
            nxt = parent.get(cur)
            if not nxt or nxt == cur or nxt in chain:
                break
            chain.append(nxt)
            cur = nxt
        if len(chain) >= THRESHOLDS[5][1] and child not in seen:
            seen.add(child)
            p, n, ln = where[child]
            out.append(Sig("deep_inheritance", p, n,
                           "继承链深度 %d：%s" % (len(chain), " -> ".join(chain)), ln,
                           "优先组合(第1章) / Strategy / State / Decorator"))
    return out


def det_single_impl_seam(files):
    decls, impls = set(), {}
    for path, lang, lines in files:
        d, im = seam_edges(lines, path)
        decls |= d
        for name, p, n, ln in im:
            impls.setdefault(name, []).append((p, n, ln))
    out = []
    for iface in sorted(decls):
        users = impls.get(iface, [])
        if len(users) == THRESHOLDS[9][1]:
            p, n, ln = users[0]
            out.append(Sig("single_impl_seam", p, n,
                           "抽象 %s 只有 1 处实现点（可能是 1 处实现 + 测试替身）" % iface, ln,
                           "第 13 章允许收回；需人工确认第二个实现是否已在 roadmap 上"))
    return out


SINGLE_FILE_DETECTORS = [det_tag_switch, det_state_branch, det_wrapper_chain, det_global_access,
                         det_noop_override, det_listener_plumbing, det_passthrough,
                         det_train_wreck, det_cross_cutting]


def scan(paths):
    files, skipped = read_files(paths)
    sigs = []
    for path, lang, lines in files:
        for d in SINGLE_FILE_DETECTORS:
            try:
                sigs.extend(d(path, lang, lines))
            except Exception as e:
                sigs.append(Sig("detector_error", path, 0, "%s 内部失败 %r（该项本次不可判读）"
                                % (d.__name__, e), "", "不得当作无信号"))
    if files:
        for d in (det_spread, det_deep_inheritance, det_single_impl_seam):
            try:
                sigs.extend(d(files))
            except Exception as e:
                sigs.append(Sig("detector_error", "(跨文件)", 0, "%s 内部失败 %r" % (d.__name__, e), "",
                                "不得当作无信号"))
    sigs.sort(key=lambda s: (s.name, s.path, s.line))
    return sigs, skipped, files


def header(files, skipped):
    by_lang = {}
    for _, lang, _ in files:
        by_lang[lang] = by_lang.get(lang, 0) + 1
    print("head-first-design-patterns · smell_scan v%s · 报结构信号，不判该不该上模式" % VERSION)
    print("扫描 %d 个文件：%s" % (len(files), " ".join("%s=%d" % kv for kv in sorted(by_lang.items()))))
    if skipped:
        print("跳过 %d 项：%s" % (len(skipped), "; ".join("%s(%s)" % kv for kv in skipped[:5])))
    print("阈值（我拍的初值，本书无任何数值判据，仅用于决定是否值得细看）："
          + " · ".join("%s=%s" % (k, v) for k, v in THRESHOLDS))
    print("覆盖：正则级非 AST；宏/代码生成/动态派发/装饰器语法糖可能漏。")
    print("已刻意不报：框架类型与值类型(struct/enum)的多点构造、行首点的流式链、"
          "NS*/UI*/URLSession 等系统单例访问点。\n")


def main(argv):
    if "--selftest" in argv:
        return selftest()
    args = [a for a in argv[1:] if not a.startswith("-")]
    if not args:
        print("用法：smell_scan.py <目录或文件…> | --selftest")
        return 2
    missing = [a for a in args if not os.path.exists(a)]
    if missing:
        for a in missing:
            print("路径不存在：%s" % a)
        print("\n本次判定作废（exit 2）：不得报'通过'，也不得报'闸门拦下了'。")
        return 2
    sigs, skipped, files = scan(args)
    header(files, skipped)
    if not files:
        print("没有受支持的文件（扩展名：%s）—— 本次判定作废（exit 2）。"
              % ",".join(sorted(LANG_BY_EXT)))
        return 2
    if not sigs:
        print("本次未发现结构信号。这只表示没有下列形状，不代表设计没问题——仍需过第 1 步的变化句。")
        print("检测项：tag_switch, state_field_branch, wrapper_chain, global_access_point, "
              "noop_override, handrolled_observer_machinery, passthrough_class, chained_getters, "
              "cross_cutting_repeat, concrete_type_spread, deep_inheritance, single_impl_seam")
        return 0
    counts = {}
    for s in sigs:
        counts[s.name] = counts.get(s.name, 0) + 1
    for s in sigs:
        print(str(s))
    print("\n汇总（共 %d 条，全部列出，未折叠）：%s"
          % (len(sigs), " · ".join("%s=%d" % kv for kv in sorted(counts.items()))))
    print("\n下一步不许跳：逐条写'成立/不成立 + 一句理由'，只把成立的当候选模式；"
          "结论里引用的数字要回到上面的行号。")
    return 1


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    fx = os.path.join(here, "fixtures")
    if not os.path.isdir(fx):
        print("夹具目录缺失：%s —— 判定作废" % fx)
        return 2
    want = {
        "ts_typeswitch.ts": {"tag_switch", "chained_getters", "global_access_point",
                             "cross_cutting_repeat", "passthrough_class"},
        "swift_state.swift": {"state_field_branch", "tag_switch", "deep_inheritance",
                              "single_impl_seam", "concrete_type_spread"},
        "py_menu.py": {"tag_switch", "handrolled_observer_machinery"},
        "java_decorator.java": {"wrapper_chain", "global_access_point"},
        "ts_chainbus.ts": {"wrapper_chain", "handrolled_observer_machinery"},
        "swift_noop.swift": {"noop_override"},
        "clean_plain.ts": set(),
        "swift_twin.swift": set(),
    }
    sigs, skipped, files = scan([fx])
    if not files:
        print("夹具扫不到文件 —— 判定作废")
        return 2
    got = {}
    for s in sigs:
        got.setdefault(os.path.basename(s.path), set()).add(s.name)
    rc = 0
    for fn in sorted(set(want) | set(got)):
        w, g = want.get(fn, set()), got.get(fn, set())
        if fn not in want:
            rc = 1
            print("FAIL %-22s 夹具未在期望表中，实得=%s" % (fn, ",".join(sorted(g))))
            continue
        if w == g:
            print("PASS %-22s %s" % (fn, ",".join(sorted(g)) or "无信号"))
        else:
            rc = 1
            print("FAIL %-22s 缺=%s 多=%s" % (fn, ",".join(sorted(w - g)) or "-",
                                             ",".join(sorted(g - w)) or "-"))
    err = [s for s in sigs if s.name == "detector_error"]
    for s in err:
        print("FAIL 检测器异常 %s" % s.detail)
        rc = 1
    print("\n夹具共 %d 条信号 / %d 个文件" % (len(sigs), len(files)))
    print("退出码：0=夹具全部吻合 · 1=有偏差或检测器异常 · 2=跑不起来")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
