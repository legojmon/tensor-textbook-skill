#!/usr/bin/env python3
"""Tensor 원고 빌더 — 구조화된 JSON 원고를 고정 부품으로 조립해 book.html 을 만든다.

    python build.py work/book.json [-o work/book.html] [--lenient] [--color]
    python build.py work/ch08.json work/ch09.json … -o work/book.html     # 여러 장을 한 책으로

원고 형식은 references/manuscript-schema.md 에 있다. 표지·목차·Preview·워밍업 문제·TOPIC·
적용문제·연습문제·실전 문제·Review·빠른 정답·해설의 HTML 은 전부 이 스크립트가 만든다. 원고에는 글만 쓴다.
필수 부품이 빠지거나 순서·분량 규칙에 어긋나면 오류를 모두 출력하고 파일을 쓰지 않는다.
--lenient 는 분량(개수) 규칙만 경고로 낮춘다. 사용자가 허락한 말이 approval.lenient 에 있어야 쓸 수 있다.
사용자의 제작 전 답과 TOPIC 구성안 승인(approval)이 없거나, 승인 뒤 구성안이 바뀌었으면 빌드하지 않는다.
만든 HTML 에는 도장(stamp.py)을 찍는다. 손으로 고친 HTML 은 render.py 가 조판하지 않는다.
"""
import argparse
import html
import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prep  # noqa: E402  배열 매크로·컬러판 그림
import stamp  # noqa: E402  build.py 도장

ALLOWED_TAGS = {"b", "i", "u", "em", "strong", "sub", "sup", "span", "br", "small", "code", "s"}
MATH = re.compile(r"\$\$.*?\$\$|\$[^$\n]*?\$", re.S)
TAG = re.compile(r"<(/?)([A-Za-z][\w-]*)([^<>]*)>")
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮"
TOPIC_RANGE = (6, 12)
# TOPIC 본문 최소 분량(한글 글자 수, 수식·태그 제외). 견본 TOPIC 01 은 약 2,300자,
# 기준에 못 미친 Codex 결과물의 TOPIC 은 약 400자였다.
MIN_TOPIC_HANGUL = 1500
MIN_BOOK_STEPS = 3          # 첫 EX 의 원서적 해법 단계 수 하한 (계산을 생략하지 않는다)
# 제작 전 확인(SKILL.md 1-B)에서 사용자에게 받은 답. 키 → 이름
APPROVAL_KEYS = {"materials": "자료 점검(장·판, 누락 자료 처리)", "scope": "범위", "exam": "시험 형식",
                 "layout": "문제 쪽 배치·출력", "figures": "그림 방식"}
PLACEHOLDER = re.compile(r"\{\{|\bTODO\b|\bTBD\b|미정|^[\s.…?·-]*$|사용자 답|여기에|예시 답", re.I)

COVER_NOTE = ("<b>Part2 「시험 개념의 완성」</b>은 Part1에서 정리한 <span class=\"tg ws\">원서 개념</span>을 시험 문제에 맞게 "
              "다시 다듬는 단계다. 강의 문제와 원서 연습문제에 반복되는 생각을 <span class=\"tg\">시험 개념</span>으로 묶고, "
              "그것이 왜 성립하는지 원서 개념으로 확인한다.")
HOWTO = [
    ("① 워밍업 문제 :", "문제 안 [준비] 칸에 풀이에 필요한 정의를 넣었다. 처음 보더라도 먼저 풀어 보고 본문으로 넘어간다."),
    ("② 본문(TOPIC) :", "<span class=\"tg\">시험 개념</span>을 하나씩 만들고, 원서 개념으로 왜 성립하는지 확인한다. 각 TOPIC의 EX 01이 워밍업 문제를 해부한다."),
    ("③ 적용문제 :", "본문의 시험 개념을 바로 써 보는 문항이다. 막히면 문제 아래 힌트를 본다."),
    ("④ 연습문제 :", "원서 장 끝 문제 중 주요 문항이다. <span class=\"tg ws\">원서적 해법</span>과 <span class=\"tg\">시험적 해법</span>을 모두 완성하는 것이 목표다."),
    ("⑤ 실전 문제 :", "시험 형식 그대로다. 시간을 재고 풀고, 답은 장 끝 빠른 정답·해설에서 확인한다."),
]
PROBLEM_SETS = {
    "warmup": ("W", "warmup", "워밍업 문제", "처음 보는 사람도 풀 수 있도록 필요한 정의를 문제 안 [준비] 칸에 넣었다.<br>본문 TOPIC의 EX 01이 이 문제들을 해부한다."),
    "apply": ("A", "a01", "TOPIC 적용문제", "TOPIC에서 만든 [시험 개념]을 바로 써 보는 문항이다.<br>원서 연습문제와 자체 제작 문항으로 구성한다."),
    "exercises": ("B", "b01", "연습문제", "원서 장 끝 문제 중 주요 문항이다.<br>가능한 모든 문제에서 [원서적 해법]과 [시험적 해법]을 완성하자."),
    "exam": ("X", "exam", "실전 문제", "시험 형식 그대로다.<br>강의 랩·실습에서 강조한 함정을 넣었다. 시간을 재고 풀어 보자."),
}
ANSWER_GROUPS = [("W", "워밍업 문제"), ("A", "TOPIC 적용문제"), ("B", "연습문제"), ("X", "실전 문제")]
CONCEPT = {"exam": ("", "시험<br>개념", 1), "book": (" book", "원서<br>개념", 0), "ind": (" ind", "간접<br>개념", 2)}
# ---- Part1 「원서 개념의 정리」: 원서 절 순서, 원서 개념·원서 간접 개념과 원서적 해법만 ----
COVER_NOTE_P1 = ("<b>Part1 「원서 개념의 정리」</b>는 강의 범위의 <span class=\"tg ws\">원서 개념</span>을 원서 절 순서대로 "
                 "정리하는 단계다. 정의와 정리를 직접 유도하고, 원서 예제와 강의 예제를 <span class=\"tg ws\">원서적 해법</span>만으로 "
                 "끝까지 푼다. Part2의 시험 개념은 모두 여기서 정리한 원서 개념 위에 세워진다.")
HOWTO_P1 = [
    ("① 본문(TOPIC) :", "원서 절 하나가 TOPIC 하나다. <span class=\"tg ws\">원서 개념</span> 박스의 정의·정리를 먼저 읽고, 유도를 손으로 따라 쓴다."),
    ("② EX :", "원서 예제와 강의 예제다. 해법을 가리고 먼저 풀어 본 뒤 <span class=\"tg ws\">원서적 해법</span>과 단계별로 맞춰 본다."),
    ("③ 확인문제 :", "원서 Exercise로 방금 정리한 개념을 바로 확인한다. 막히면 문제 아래 힌트를 본다."),
    ("④ 연습문제 :", "원서 장 끝 문제 중 기본 문항이다. 원서의 방식대로 끝까지 풀어 답을 맞춘다."),
    ("⑤ Review :", "O/X 개념진단으로 원서를 보지 않고 정의·유도를 할 수 있는지 확인한 뒤 Part2로 넘어간다."),
]
PROBLEM_SETS_P1 = {
    "apply": ("A", "a01", "확인문제", "원서 Exercise로 본문의 [원서 개념]을 바로 확인하는 문항이다.<br>원서의 방식대로 끝까지 풀어 보자."),
    "exercises": ("B", "b01", "연습문제", "원서 장 끝 문제 중 기본 문항이다.<br>모든 문제를 [원서적 해법]으로 완성하자."),
}
ANSWER_GROUPS_P1 = [("E", "본문 EX"), ("A", "확인문제"), ("B", "연습문제")]
ORDER_P1_FORBIDDEN = {"sol.exam": "시험적 해법", "concept": "시험 개념 박스", "grade": "채점 포인트", "vs": "강의 VS 연습문제 표"}
ORDER = ["ex", "sol.book", "bubble", "sol.exam", "concept", "core"]
ORDER_NAME = {"ex": "EX", "sol.book": "원서적 해법", "bubble": "말풍선", "sol.exam": "시험적 해법",
              "concept": "시험 개념 박스", "core": "CORE", "grade": "채점 포인트", "vs": "강의 VS 연습문제 표"}


class Builder:
    def __init__(self, data, out_dir, lenient=False):
        self.d = data
        self.out_dir = out_dir
        self.lenient = lenient
        self.errors, self.warnings = [], []
        self.labels = []          # 정답이 필요한 번호: W·01, 01-EX01, A·01, B·01, X·01 …
        self.sources = data.get("sources") or {}
        self.p1 = str(data.get("part", "Part2")) == "Part1"

    # ---------- 진단 ----------
    def err(self, where, msg):
        self.errors.append(f"[오류] {where}: {msg}")

    def count(self, where, msg):
        """분량 규칙. --lenient 에서는 경고."""
        if self.lenient:
            self.warnings.append(f"[경고] {where}: {msg}")
        else:
            self.errors.append(f"[분량] {where}: {msg}")

    # ---------- 글 ----------
    def inline(self, s, where):
        if not isinstance(s, str):
            self.err(where, f"문자열이어야 한다: {type(s).__name__}")
            return ""
        if s.count("$") % 2:
            self.err(where, "$ 짝이 맞지 않음")
        parts, pos = [], 0
        for m in MATH.finditer(s):
            parts.append(self.text(s[pos:m.start()], where))
            parts.append(html.escape(m.group(0), quote=False))
            pos = m.end()
        parts.append(self.text(s[pos:], where))
        return "".join(parts)

    def text(self, t, where):
        def tag(m):
            name = m.group(2).lower()
            if name not in ALLOWED_TAGS:
                self.err(where, f"허용되지 않는 태그 <{name}> (블록은 JSON 부품으로 쓴다)")
            if re.search(r"\bstyle\s*=", m.group(3), re.I):
                self.err(where, "style 속성 금지 (조판은 CSS 가 정한다)")
            return m.group(0)
        t = TAG.sub(tag, t)
        return re.sub(r"<(?![/A-Za-z])", "&lt;", t)

    def plain(self, s, where):
        if not isinstance(s, str):
            self.err(where, "문자열이어야 한다")
            return ""
        return html.escape(s, quote=True)

    def need(self, obj, key, where, kind=str):
        v = obj.get(key) if isinstance(obj, dict) else None
        if v is None or v == "" or v == []:
            self.err(where, f"'{key}' 없음")
            return "" if kind is str else ([] if kind is list else "")
        if not isinstance(v, kind):
            name = kind.__name__ if isinstance(kind, type) else "/".join(k.__name__ for k in kind)
            self.err(where, f"'{key}' 는 {name} 이어야 한다")
            return "" if kind is str else ([] if kind is list else "")
        return v

    # ---------- 그림 ----------
    def fig(self, spec, where, default_width, cls="fig"):
        """spec: {src,width,cap} 또는 그 목록. 없으면 ''."""
        if not spec:
            return ""
        items = spec if isinstance(spec, list) else [spec]
        out = []
        for it in items:
            if isinstance(it, str):
                it = {"src": it}
            src = self.need(it, "src", where)
            if src and not (self.out_dir / src).is_file():
                self.err(where, f"그림 파일 없음: {src} (출력 폴더 기준)")
            elif src:
                self.check_fig_origin(it, src, where)
            width = it.get("width", default_width)
            if not re.fullmatch(r"\d+(\.\d+)?mm", str(width)):
                self.err(where, f"그림 폭은 'NNmm' 형식: {width}")
            out.append(f'<img src="{html.escape(src)}" style="width:{width}">')
            if it.get("cap"):
                out.append(f'<div class="cap">{self.inline(it["cap"], where + " 그림 설명")}</div>')
        return f'<div class="{cls}">{"".join(out)}</div>'

    def figure_or_reason(self, obj, where, default_width):
        if obj.get("fig"):
            return self.fig(obj["fig"], where, default_width)
        if not obj.get("nofig"):
            self.err(where, "그림(fig) 없음. 그림이 필요 없는 문제이면 nofig 에 이유를 쓴다")
        return ""

    def check_fig_origin(self, it, src, where):
        """그림마다 원본(from)을 밝힌다. 원서·강의 그림을 SVG 로 다시 그렸으면 대조 시트가 있어야 한다."""
        origin = it.get("from")
        if not isinstance(origin, str) or not origin.strip():
            self.err(where, f"그림 {src} 의 원본(from) 없음. 예: \"원서 Fig 14.7-6 p.747\", \"강의 p.12\", \"자체 제작\"")
            return
        origin = origin.strip()
        if origin.startswith("자체 제작"):
            return
        self.check_src(origin, f"{where} 그림 원본")
        path = self.out_dir / src
        if path.suffix.lower() != ".svg":      # 원본을 잘라 흑백 보정한 그림(figtools crop/mono)
            return
        sheet = self.out_dir / "compare" / f"{path.stem}.png"
        if not sheet.is_file():
            self.err(where, f"다시 그린 그림 {src} 의 대조 시트 없음 → python <skill>/scripts/figtools.py compare <원본.png> {src} "
                            f"-o compare/{path.stem}.png 로 만들고 열어서 값·라벨·방향·연결을 확인한다")
        elif sheet.stat().st_mtime < path.stat().st_mtime:
            self.err(where, f"대조 시트 compare/{path.stem}.png 가 {src} 보다 오래됨. 그림을 고쳤으면 다시 대조한다")

    # ---------- 단위 부품 (해법·개념 박스 안) ----------
    def units(self, items, where, counter=None, default_n="·"):
        """items: 문자열(단계) 또는 {step|p|fig|withfig|table|code|steps}. counter: 단계 번호 자동 매김용 list."""
        if isinstance(items, str):
            items = [items]
        if not isinstance(items, list):
            self.err(where, "units 는 목록이어야 한다")
            return ""
        out = []
        for i, it in enumerate(items):
            w = f"{where} 단위 {i + 1}"
            if isinstance(it, str):
                it = {"step": it}
            if not isinstance(it, dict):
                self.err(w, "문자열 또는 객체여야 한다")
                continue
            if "step" in it:
                if "n" in it:
                    n = str(it["n"])
                elif counter is not None:
                    n = CIRCLED[len(counter)] if len(counter) < len(CIRCLED) else str(len(counter) + 1)
                    counter.append(n)
                else:
                    n = default_n
                out.append(f'<div class="step"><span class="n">{html.escape(n)}</span><span>{self.inline(it["step"], w)}</span></div>')
            elif "p" in it:
                out.append(f'<p>{self.inline(it["p"], w)}</p>')
            elif "fig" in it:
                out.append(self.fig(it["fig"], w, "62mm"))
            elif "withfig" in it:
                wf = it["withfig"]
                inner = self.units(wf.get("units", []), w, counter, default_n)
                out.append(f'<div class="withfig"><div class="txt">{inner}</div>{self.fig(wf.get("fig"), w, "62mm")}</div>')
            elif "table" in it:
                out.append(self.table(it["table"], w))
            elif "code" in it:
                out.append(self.code(it, w))
            elif "steps" in it:
                out.append(self.units(it["steps"], w, None, it.get("n", "·")))
            else:
                self.err(w, f"알 수 없는 단위: {list(it)[:3]}")
        return "".join(out)

    def table(self, t, where):
        head = t.get("head") or []
        rows = self.need(t, "rows", where, list)
        h = "<tr>" + "".join(f"<th>{self.inline(c, where)}</th>" for c in head) + "</tr>" if head else ""
        body = "".join("<tr>" + "".join(f"<td>{self.inline(c, where)}</td>" for c in r) + "</tr>" for r in rows)
        return f"<table>{h}{body}</table>"

    def code(self, it, where):
        txt = it["code"] if isinstance(it.get("code"), str) else self.need(it, "text", where)
        cap = f'<div class="cap">{self.inline(it["cap"], where)}</div>' if it.get("cap") else ""
        body = html.escape(txt).replace("[[b]]", "<b>").replace("[[/b]]", "</b>")
        return f'<pre class="code">{body}</pre>{cap}'

    # ---------- TOPIC 블록 ----------
    def block(self, b, t, where):
        if isinstance(b, str):
            if b.startswith("## "):
                b = {"type": "h3", "text": b[3:]}
            elif b.startswith("### "):
                b = {"type": "h4", "text": b[4:]}
            else:
                b = {"type": "p", "text": b}
        kind = b.get("type")
        if kind == "p":
            cls = ' class="keep-next"' if b.get("keep_next") else ""
            return "p", f'<p{cls}>{self.inline(self.need(b, "text", where), where)}</p>'
        if kind in ("h3", "h4"):
            return kind, f'<{kind}>{self.inline(self.need(b, "text", where), where)}</{kind}>'
        if kind == "flow":
            chips = self.need(b, "chips", where, list)
            cs = []
            for i, c in enumerate(chips):
                cls = "c end" if i == len(chips) - 1 else "c"
                cs.append(f'<span class="{cls}">{self.inline(c, where)}</span>')
            arrow = '<span class="ar">→</span>'
            out = f'<div class="flow">{arrow.join(cs)}</div>'
            if b.get("rev"):
                out += f'<div class="rev"><span class="line"></span><br>{self.inline(b["rev"], where)}</div>'
            return "flow", out
        if kind == "ex":
            t["ex"] += 1
            no = f"{t['ex']:02d}"
            self.labels.append(f"{t['no']}-EX{no}")
            src = b.get("src")
            if isinstance(src, str):
                src = [src]
            if not src:
                self.err(where, "출처(src) 없음. 예: [\"원서 Example 14.7-1\", \"강의 p.12\"]")
                src = []
            self.check_src(" · ".join(src), f"{where} 출처")
            srch = "<br>".join(self.inline(s, where) for s in src)
            figh = self.figure_or_reason(b, where, "60mm")
            txt = f'<div class="txt q">{self.inline(self.need(b, "text", where), where)}</div>'
            body = f'<div class="withfig">{txt}{figh}</div>' if figh else txt
            return "ex", (f'<div class="ex"><div><span class="badge">EX<span>{no}</span></span>'
                          f'<div class="src">[{srch}]</div></div>{body}</div>')
        if kind == "sol":
            k = b.get("kind", "book")
            if k not in ("book", "exam"):
                self.err(where, "sol.kind 는 book(원서적) 또는 exam(시험적)")
                k = "book"
            counter = []
            inner = self.units(b.get("units", []), where, counter)
            if not inner:
                self.err(where, "해법 내용(units) 없음")
            if k == "book" and t["ex"] == 1 and not t.get("book_checked"):
                t["book_checked"] = True
                steps = inner.count('<div class="step">')
                if steps < MIN_BOOK_STEPS:
                    self.count(where, f"첫 EX 의 원서적 해법은 {MIN_BOOK_STEPS}단계 이상 ({steps}단계). 원서 방식 그대로, 계산을 생략하지 않는다")
            if k == "exam":
                cond = b.get("cond")
                if not cond:
                    self.err(where, "시험적 해법에 적용 조건(cond) 없음")
                inner = f'<div class="cond"><b>적용 조건</b>{self.inline(cond or "", where)}</div>' + inner
            a = "원서적" if k == "book" else "시험적"
            cls = "sol" if k == "book" else "sol exam"
            return f"sol.{k}", (f'<div class="{cls}"><span class="lab"><span class="a">{a}</span><span class="b">해법</span></span>'
                                f'<div class="box">{inner}</div></div>')
        if kind == "bubble":
            return "bubble", f'<div class="bubble"><span class="dots">∘○</span><span class="b">{self.inline(self.need(b, "text", where), where)}</span></div>'
        if kind == "steps":
            return "steps", self.units(b.get("units", []), where, None, b.get("n", "·"))
        if kind == "fn":
            key = b.get("key", "ⓐ")
            return "fn", f'<div class="fn"><span class="k">{html.escape(key)}</span> {self.inline(self.need(b, "text", where), where)}</div>'
        if kind == "concept":
            k = b.get("kind", "exam")
            if k not in CONCEPT:
                self.err(where, "concept.kind 는 exam / book / ind")
                k = "exam"
            cls, ico, on = CONCEPT[k]
            tabs = "".join(f'<span class="on">{n}</span>' if i == on else f"<span>{n}</span>"
                           for i, n in enumerate(["원서 개념", "시험 개념", "원서 간접 개념"]))
            inner = self.units(b.get("units", []), where, [] if b.get("numbered", True) else None)
            if not inner:
                self.err(where, "개념 박스 내용(units) 없음 (표 또는 번호 절차)")
            if k == "exam":
                if not b.get("cond"):
                    self.err(where, "시험 개념 박스에 적용 조건(cond) 없음")
                inner += f'<div class="cond"><b>적용 조건</b>{self.inline(b.get("cond", ""), where)}</div>'
            elif b.get("cond"):
                inner += f'<div class="cond"><b>적용 조건</b>{self.inline(b["cond"], where)}</div>'
            title = self.inline(self.need(b, "title", where), where)
            return ("concept" if k == "exam" else f"concept.{k}"), (
                f'<div class="concept{cls}"><div class="hd"><div class="ttl"><span class="ico">{ico}</span>{title}</div>'
                f'<div class="tabs">{tabs}</div></div><div class="body">{inner}</div></div>')
        if kind == "core":
            cond = self.inline(self.need(b, "cond", where), where)
            act = self.inline(self.need(b, "action", where), where)
            return "core", f'<div class="core"><span class="lab">CORE</span><div class="box">[{cond}] ⟹ [{act}]</div></div>'
        if kind == "tip":
            t["tip"] += 1
            body = f'<p>{self.inline(b["text"], where)}</p>' if b.get("text") else self.units(b.get("units", []), where)
            if not body:
                self.err(where, "TIP 본문(text) 없음")
            return "tip", (f'<div class="tip"><div class="lab"><small>저자의 특강</small><b>TIP</b></div>'
                           f'<div class="hd">{self.inline(self.need(b, "title", where), where)}</div><div class="body">{body}</div></div>')
        if kind == "grade":
            items = self.need(b, "items", where, list)
            if not 4 <= len(items) <= 6:
                self.count(where, f"채점 포인트는 4~6줄 ({len(items)}줄)")
            intro = f'<p>{self.inline(b["intro"], where)}</p>' if b.get("intro") else ""
            if not intro:
                self.err(where, "채점 포인트 첫 문단(intro: 이 유형이 어떻게 채점되는지) 없음")
            ol = "".join(f"<li>{self.inline(x, where)}</li>" for x in items)
            return "grade", (f'<div class="grade"><div class="hd"><span>✎ 답안 · 채점 포인트</span><small>대학 시험 특화</small></div>'
                             f'<div class="body">{intro}<ol>{ol}</ol></div></div>')
        if kind == "vs":
            rows = self.need(b, "rows", where, list)
            if not 4 <= len(rows) <= 6:
                self.count(where, f"강의 VS 연습문제 표는 4~6행 ({len(rows)}행)")
            trs = []
            for r in rows:
                if not (isinstance(r, list) and len(r) == 2):
                    self.err(where, "표의 행은 [출처, 출제 요소] 두 칸")
                    continue
                trs.append(f"<tr><td>{self.inline(r[0], where)}</td><td>{self.inline(r[1], where)}</td></tr>")
            out = (f'<div class="vs"><span class="lab">강의 <span class="v">VS</span> 연습문제</span>'
                   f'<table><tr><th>출처</th><th>출제 요소</th></tr>{"".join(trs)}</table></div>')
            if b.get("after"):
                out += f'<p>{self.inline(b["after"], where)}</p>'
            else:
                self.err(where, "표 뒤 마무리 문장(after) 없음")
            return "vs", out
        if kind == "fig":
            return "fig", self.fig(b, where, "62mm")
        if kind == "code":
            return "code", self.code(b, where)
        if kind == "table":
            return "table", self.table(b, where).replace("<table>", '<table class="tb">', 1)
        if kind == "pagebreak":
            return "pagebreak", '<div class="pagebreak"></div>'
        self.err(where, f"알 수 없는 블록 type: {kind!r}")
        return "?", ""

    def topic(self, tp, idx):
        where = f"TOPIC {tp.get('no', idx + 1)}"
        no = str(self.need(tp, "no", where, (str, int)))
        title = self.need(tp, "title", where)
        blocks = self.need(tp, "blocks", where, list)
        t = {"no": no, "ex": 0, "tip": 0}
        kinds, parts = [], []
        for i, b in enumerate(blocks):
            k, h = self.block(b, t, f"{where} 블록 {i + 1}")
            kinds.append(k)
            parts.append(h)
        (self.check_topic_p1 if self.p1 else self.check_topic)(kinds, where, t)
        hangul = len(re.findall(r"[가-힣]", TAG.sub(" ", MATH.sub(" ", html.unescape("\n".join(parts))))))
        if hangul < MIN_TOPIC_HANGUL:
            self.count(where, f"본문이 너무 짧다: 한글 {hangul}자 (최소 {MIN_TOPIC_HANGUL}자, 견본 TOPIC 01 은 약 2,300자). "
                              "도입·관찰·논증 문단과 EX 02·03 을 견본 밀도로 쓴다")
        ox = tp.get("ox")
        if not isinstance(ox, list) or not 3 <= len(ox) <= 5:
            self.count(where, f"Review O/X 문항(ox)은 3~5개 ({len(ox) if isinstance(ox, list) else 0}개)")
        return (f'<section class="topic" data-no="{html.escape(no)}" data-title="{html.escape(title, quote=True)}">\n'
                + "\n".join(parts) + "\n</section>")

    def check_topic(self, kinds, where, t):
        first = {k: kinds.index(k) for k in set(kinds)}
        for k in ORDER + ["grade", "vs"]:
            if k not in first:
                self.err(where, f"{ORDER_NAME[k]} 없음")
        if "h3" not in first:
            self.err(where, "소절 제목(h3) 없음")
        elif kinds.count("h3") < 2:
            self.count(where, f"소절 제목(h3)은 TOPIC당 2~3개 ({kinds.count('h3')}개)")
        if t["ex"] < 2:
            self.count(where, f"EX 는 TOPIC당 2~3개 ({t['ex']}개)")
        if "ex" in first and "p" not in kinds[:first["ex"]]:
            self.err(where, "첫 EX 앞에 도입 문단(근거 번호 포함)이 없음")
        if "ex" in first and (first["ex"] + 1 >= len(kinds) or kinds[first["ex"] + 1] != "sol.book"):
            self.err(where, "첫 EX 바로 다음은 원서적 해법이어야 한다")
        if all(k in first for k in ("sol.book", "bubble")):
            if "p" not in kinds[first["sol.book"] + 1:first["bubble"]]:
                self.err(where, "원서적 해법과 말풍선 사이에 관찰 문단이 없음")
        chain = [first[k] for k in ORDER if k in first]
        if chain != sorted(chain):
            self.err(where, "부품 순서가 틀림: EX → 원서적 해법 → 말풍선 → 시험적 해법 → 시험 개념 박스 → CORE")
        for k in ("grade", "vs"):
            if k in first and "concept" in first and first[k] < first["concept"]:
                self.err(where, f"{ORDER_NAME[k]}는 시험 개념 박스 뒤에 둔다")
        if t["tip"] > 1:
            self.count(where, f"TIP 은 TOPIC당 1개 이하 ({t['tip']}개)")

    def check_topic_p1(self, kinds, where, t):
        """Part1: 소절 제목 → 도입 문단 → (원서 개념 박스) → EX → 원서적 해법 … → CORE. 시험 부품은 넣지 않는다."""
        first = {k: kinds.index(k) for k in set(kinds)}
        for k, name in ORDER_P1_FORBIDDEN.items():
            if k in first:
                self.err(where, f"Part1 에는 {name}를 넣지 않는다 (원서 개념·원서적 해법만)")
        if "concept.book" not in first:
            self.err(where, "원서 개념 박스(concept kind book) 없음: 이 절의 정의·정리를 박스로 정리한다")
        for k, name in (("ex", "EX"), ("sol.book", "원서적 해법"), ("core", "CORE")):
            if k not in first:
                self.err(where, f"{name} 없음")
        if "h3" not in first:
            self.err(where, "소절 제목(h3) 없음")
        elif kinds.count("h3") < 2:
            self.count(where, f"소절 제목(h3)은 TOPIC당 2~3개 ({kinds.count('h3')}개)")
        if t["ex"] < 2:
            self.count(where, f"EX 는 TOPIC당 2~3개 ({t['ex']}개)")
        lead = min([first[k] for k in ("ex", "concept.book") if k in first] or [0])
        if "p" not in kinds[:lead]:
            self.err(where, "첫 원서 개념 박스·EX 앞에 도입 문단(원서 절·강의 쪽 근거 포함)이 없음")
        for i, k in enumerate(kinds):
            if k == "ex" and (i + 1 >= len(kinds) or kinds[i + 1] != "sol.book"):
                self.err(where, f"EX 바로 다음은 원서적 해법이어야 한다 (블록 {i + 2})")
        if "core" in first and "concept.book" in first and first["core"] < first["concept.book"]:
            self.err(where, "CORE 는 원서 개념 박스 뒤에 둔다")
        if t["tip"] > 1:
            self.count(where, f"TIP 은 TOPIC당 1개 이하 ({t['tip']}개)")

    # ---------- 출처 ----------
    def check_src(self, src, where):
        if not self.sources or src.strip().startswith("실전"):   # 실전 문제: '실전 · 근거'
            return
        for p in [p.strip() for p in re.split(r"\s[·/]\s|,", src) if p.strip()]:
            if p.startswith(("자체 제작", "실전", "= ")):
                continue
            key = next((k for k in self.sources if p.startswith(k)), None)
            if not key:
                self.err(where, f"'{p}': sources 에 선언된 이름({', '.join(self.sources)}) 또는 '자체 제작'으로 시작해야 한다")
                continue
            chapters = (self.sources[key] or {}).get("chapters")
            if chapters:
                allowed = {str(c) for c in chapters}
                for m in re.finditer(r"(?<![\d.])(\d{1,2})[.\-]\d+", p):
                    if m.group(1) not in allowed:
                        self.err(where, f"'{p}': {key}의 장 번호 {m.group(1)}은 선언된 장({', '.join(sorted(allowed))})이 아니다")

    # ---------- 문제 ----------
    def problems(self, key, items, topics_built, scope):
        sets = PROBLEM_SETS_P1 if self.p1 else PROBLEM_SETS
        if key not in sets:
            if items:
                self.err(key, f"Part1 에는 {PROBLEM_SETS[key][2]}({PROBLEM_SETS[key][0]})를 넣지 않는다 (확인문제 A·연습문제 B 만)")
            return ""
        prefix, pid, title, desc = sets[key]
        if not items:
            return ""
        out = []
        for i, q in enumerate(items):
            label = f"{prefix}·{i + 1:02d}"
            where = label
            self.labels.append(label)
            lv = q.get("lv", 1)
            if lv not in (1, 2, 3):
                self.err(where, "난이도 lv 는 1~3")
            src = self.need(q, "src", where)
            self.check_src(src, f"{where} 출처")
            topic = str(q.get("topic") or "")
            if not topic:
                self.err(where, "관련 TOPIC(topic) 없음")
            elif topic not in topics_built:
                if scope == "chapter":
                    self.err(where, f"관련 TOPIC {topic} 은 이 원고에 없음")
                else:
                    self.warnings.append(f"[경고] {where}: 관련 TOPIC {topic} 은 이 시안에 없음")
            hint = self.need(q, "hint", where)
            figh = self.figure_or_reason(q, where, "62mm")
            txt = self.inline(self.need(q, "text", where), where)
            if key == "warmup":
                pre = self.need(q, "pre", where)
                txt = f'<div class="pre"><b>준비</b>{self.inline(pre, where + " 준비")}</div>{txt}'
            out.append(f'<div class="qitem" data-no="{label}" data-lv="{lv}" data-src="{html.escape(src, quote=True)}" '
                       f'data-topic="{html.escape(topic, quote=True)}" data-hint="{html.escape(hint, quote=True)}">'
                       f'<div class="t">{txt}</div>{figh}</div>')
        extra = self.d.get(key + "_note")
        if extra:
            desc += " " + self.inline(extra, key + "_note")
        per = self.d.get("per_page", 2)
        if per not in (2, 4):
            self.err("per_page", "쪽당 문제 수는 2 또는 4")
        return (f'<section class="problems" data-id="{pid}" data-title="{title}" data-desc="{html.escape(desc, quote=True)}" data-per="{per}">\n'
                + "\n".join(out) + "\n</section>")

    # ---------- 고정 쪽 ----------
    @staticmethod
    def page_head(tag):
        return f'<div class="pv-head"><span class="tag">{tag}</span></div>'

    def review_pages(self, rv, plan_built, chapter, chtitle):
        where = "review"
        paras = self.need(rv, "paragraphs", where, list)
        if len(paras) != 2:
            self.count(where, f"Review OVERVIEW 는 2문단 ({len(paras)}문단)")
        box = (f'<div class="pv-box"><div class="pv-ico"><span class="fig8">∑</span>OVER–<br>VIEW</div>'
               + "".join(f"<p>{self.inline(p, where)}</p>" for p in paras) + "</div>")
        rows = []
        for tp in plan_built:
            items = tp.get("ox") or []
            li = "".join(f"<li>{self.inline(x, f'TOPIC {tp['no']} ox')}</li>" for x in items)
            rows.append((f'<tr><td class="tp">TOPIC {tp["no"]}<br>{self.inline(tp["title"], where)}</td>'
                         f'<td class="pg" data-ref="topic-{tp["no"]}"></td><td><ul>{li}</ul></td></tr>',
                         4 + 5.5 * max(len(items), 1)))
        budget_first, budget_next = rv.get("first_page_mm", 150), rv.get("page_mm", 235)
        pages, cur, used, budget = [], [], 0, budget_first
        for r, h in rows:
            if cur and used + h > budget:
                pages.append(cur)
                cur, used, budget = [], 0, budget_next
            cur.append(r)
            used += h
        pages.append(cur)
        out = []
        for i, pg in enumerate(pages):
            table = f'<table class="ox">{"".join(pg)}</table>'
            if i == 0:
                out.append(f'<section class="page" data-id="review" data-run="Review: 개념진단">{self.page_head("Review: 개념진단")}'
                           f'<div class="pv-frame"><div class="pv-title"><span class="n">{chapter}</span>{chtitle}</div>{box}</div>'
                           f'<div class="ox-wrap"><div class="ox-title">✓ TOPIC 본문 O/X</div>{table}</div></section>')
            else:
                out.append(f'<section class="page" data-run="Review: 개념진단">{self.page_head("Review: 개념진단")}'
                           f'<div class="ox-wrap"><div class="ox-title">✓ TOPIC 본문 O/X (계속)</div>{table}</div></section>')
        return "\n".join(out)

    def answer_section(self, answers):
        """빠른 정답·해설: Review 뒤에 자동 쪽 나눔되는 장. W(+EX) → A → B → X 순서."""
        where = "answers"
        if not isinstance(answers, list):
            self.err(where, "answers 는 목록이어야 한다 (모든 W·EX·A·B·X 의 답)")
            answers = []
        agroups = ANSWER_GROUPS_P1 if self.p1 else ANSWER_GROUPS
        covered, groups = set(), {g: [] for g, _ in agroups}
        for i, a in enumerate(answers):
            w = f"{where} {i + 1}"
            keys = a.get("for")
            if isinstance(keys, str):
                keys = [keys]
            if not keys:
                self.err(w, "'for' 없음 (예: [W·01, 01-EX01])")
                keys = []
            for k in keys:
                if k not in self.labels:
                    self.err(w, f"'{k}' 은 이 원고의 문제 번호가 아님 (예: {', '.join(self.labels[:5])})")
                covered.add(k)
            label = a.get("label") or " / ".join(re.sub(r"^(\d+)-EX(\d+)$", r"TOPIC \1 · EX \2" if self.p1 else r"EX \2", k) for k in keys)
            body = self.inline(self.need(a, "text", w), w)
            if a.get("code"):
                body += self.code({"code": a["code"]}, w)
            group = next((k[0] for k in keys if k[0] in groups), "E" if self.p1 else "W")
            groups[group].append(f'<p><b>{self.inline(label, w)}</b> {body}</p>')
        missing = [k for k in self.labels if k not in covered]
        if missing:
            self.err(where, f"빠른 정답이 없는 문제: {', '.join(missing)}")
        parts = [f"<h3>{name}</h3>" + "".join(groups[g]) for g, name in agroups if groups[g]]
        return ('<article class="manuscript">\n<section class="topic" data-no="해설" data-title="빠른 정답·해설">\n'
                + "\n".join(parts) + "\n</section>\n</article>")

    # ---------- 전체 ----------
    def build(self):
        d = self.d
        scope = d.get("scope", "chapter")
        if scope not in ("chapter", "draft"):
            self.err("scope", "chapter(장 전체) 또는 draft(TOPIC 시안)")
        subject = self.plain(self.need(d, "subject", "subject"), "subject")
        ch = d.get("chapter") or {}
        chapter = self.plain(str(self.need(ch, "no", "chapter", (str, int))), "chapter")
        chtitle = self.inline(self.need(ch, "title", "chapter"), "chapter")
        title_en = self.inline(ch.get("title_en", ""), "chapter")
        start = d.get("start_page", 1)
        if not isinstance(start, int) or start < 1:
            self.err("start_page", "1 이상의 정수")
        part = d.get("part", "Part2")
        topics = self.need(d, "topics", "topics", list)
        plan = d.get("plan") or [{"no": t.get("no"), "title": t.get("title")} for t in topics]
        built = {str(t.get("no")): t for t in topics}
        plan_nos = [str(p.get("no")) for p in plan]
        for no in plan_nos:
            if not no.isdigit():
                self.err("plan", f"TOPIC 번호 '{no}' 는 숫자(01, 02 …)여야 한다")
        for no in built:
            if no not in plan_nos:
                self.err(f"TOPIC {no}", "plan(TOPIC 구성안)에 없는 TOPIC")
        if scope == "chapter":
            missing = [n for n in plan_nos if n not in built]
            if missing:
                self.err("topics", f"장 전체(scope: chapter)인데 구성안의 TOPIC {', '.join(missing)} 원고가 없음. 시안이면 scope 를 draft 로")
            if not TOPIC_RANGE[0] <= len(topics) <= TOPIC_RANGE[1]:
                self.count("topics", f"장 전체의 TOPIC 은 {TOPIC_RANGE[0]}~{TOPIC_RANGE[1]}개 ({len(topics)}개). 승인받은 구성안과 맞춘다")
        elif not topics:
            self.err("topics", "TOPIC 원고가 하나도 없음")
        self.check_approval(d.get("approval"), plan)

        theme = "" if d.get("theme") == "color" else '<link rel="stylesheet" href="tensor://css/theme-mono.css">\n'
        head = (f'<!DOCTYPE html>\n<html lang="ko"><head><meta charset="utf-8">\n<title>{subject} {part} Ch{chapter} — Tensor</title>\n'
                '<link rel="stylesheet" href="tensor://katex/katex.min.css">\n<link rel="stylesheet" href="tensor://pretendard/pretendard.css">\n'
                '<link rel="stylesheet" href="tensor://css/tensor.css">\n' + theme +
                '<script src="tensor://katex/katex.min.js"></script>\n<script src="tensor://katex/contrib/auto-render.min.js"></script>\n'
                '<script src="tensor://css/paginate.js"></script>\n</head>\n'
                f'<body data-chapter="{chapter}" data-chtitle="{html.escape(str(ch.get("title", "")), quote=True)}" '
                f'data-part="{html.escape(part)}" data-start="{start}">\n'
                '<!-- tensor build.py 가 만든 파일. 손으로 고치지 말고 JSON 원고를 고친다. -->\n')
        note = (COVER_NOTE_P1 if self.p1 else COVER_NOTE) + (f' <br><span class="note-extra">{self.inline(d["cover_note"], "cover_note")}</span>' if d.get("cover_note") else "")
        cover = (f'<!-- FRONTMATTER -->\n<section class="page cover" data-chapter="{chapter}" data-part="{html.escape(part)}" '
                 f'data-chtitle="{html.escape(str(ch.get("title", "")), quote=True)}">'
                 '<div class="brand">TENSOR</div><div class="arch"></div><div class="chap">CHAPTER</div>'
                 f'<div class="num">{chapter}</div><div class="ttl">{chtitle}<small>{title_en}</small></div><div class="note">{note}</div></section>')
        rows = [f'<tr><td class="c1">{chapter}. {chtitle}</td><td class="pc">Preview</td><td class="pg" data-ref="preview"></td></tr>']
        for p in plan:
            no, ttl = str(p.get("no")), self.inline(str(p.get("title", "")), "plan")
            pg = f'<td class="pg" data-ref="topic-{no}"></td>' if no in built else '<td class="pg muted">—</td>'
            rows.append(f'<tr><td></td><td>TOPIC {no}. {ttl}</td>{pg}</tr>')
        if d.get("warmup"):
            rows.insert(1, '<tr><td></td><td class="pc">W·01 워밍업 문제</td><td class="pg" data-ref="warmup"></td></tr>')
        if d.get("apply"):
            rows.append(f'<tr><td></td><td class="pc">A·01{" 확인문제" if self.p1 else ""}</td><td class="pg" data-ref="a01"></td></tr>')
        if d.get("exercises"):
            rows.append(f'<tr><td></td><td class="pc">B·01{" 연습문제" if self.p1 else ""}</td><td class="pg" data-ref="b01"></td></tr>')
        if d.get("exam"):
            rows.append('<tr><td></td><td class="pc">X·01 실전 문제</td><td class="pg" data-ref="exam"></td></tr>')
        rows.append('<tr><td></td><td class="pc">Review</td><td class="pg" data-ref="review"></td></tr>')
        rows.append('<tr><td></td><td class="pc">빠른 정답·해설</td><td class="pg" data-ref="topic-해설"></td></tr>')
        toc = (f'<section class="page toc"><div class="panel"></div><div class="circle">Chapter<b>{chapter}</b></div><div class="list">'
               + (f'<div class="hdr">{subject} 원서 개념의 정리 &nbsp;<small>: 강의 범위의 [원서 개념]을 원서 순서대로</small></div>' if self.p1 else
                  f'<div class="hdr">{subject} 시험 개념의 완성 &nbsp;<small>: Part1 정리 + 시험에 꼭 필요한 [시험 개념]</small></div>')
               + f'<table>{"".join(rows)}</table></div></section>')
        pv = d.get("preview") or {}
        paras = self.need(pv, "paragraphs", "preview", list)
        if len(paras) != 3:
            self.count("preview", f"Preview 는 3문단 ({len(paras)}문단): 장의 역할 / 반복 구조와 첫 TOPIC / 나머지 TOPIC")
        howto = "".join(f'<div class="k">{k}</div><div>{v}</div>' for k, v in (HOWTO_P1 if self.p1 else HOWTO))
        preview = (f'<section class="page" data-id="preview">{self.page_head("Preview")}'
                   f'<div class="pv-frame"><div class="pv-title"><span class="n">{chapter}</span>{chtitle}</div>'
                   f'<div class="pv-box"><div class="pv-ico"><span class="fig8">∑</span>PRE–<br>VIEW</div>'
                   + "".join(f"<p>{self.inline(p, 'preview')}</p>" for p in paras)
                   + f'<p class="sans howto-title">〈학습 방법〉</p><div class="howto">{howto}</div></div></div>'
                   '<div class="memo">MEMO</div></section>')
        warmup = self.problems("warmup", d.get("warmup") or [], built, scope)
        body = "\n".join(self.topic(t, i) for i, t in enumerate(topics))
        apply_ = self.problems("apply", d.get("apply") or [], built, scope)
        exercises = self.problems("exercises", d.get("exercises") or [], built, scope)
        exam = self.problems("exam", d.get("exam") or [], built, scope)
        self.check_problem_counts(d, built, scope)
        plan_built = [dict(p, ox=built[str(p.get("no"))].get("ox")) for p in plan if str(p.get("no")) in built]
        review = self.review_pages(d.get("review") or {}, plan_built, chapter, chtitle)
        answers = self.answer_section(d.get("answers"))
        return "\n\n".join(x for x in [head + cover, toc, preview, warmup, f'<article class="manuscript">\n{body}\n</article>',
                                       apply_, exercises, exam, review, answers, "</body></html>\n"] if x)

    def check_approval(self, ap, plan):
        """제작 전 확인(1-B)과 TOPIC 구성안 승인(2단계)을 사용자에게 받았는지. 사용자의 말을 그대로 옮긴 기록이 있어야 빌드한다."""
        where = "approval"
        hint = ("제작 전 질문과 TOPIC 구성안을 사용자에게 보여 주고 답을 받은 뒤, 사용자의 말을 그대로 approval 에 옮긴다 "
                "(manuscript-schema.md §2). 답을 받기 전에는 원고를 쓰지 않는다")
        if not isinstance(ap, dict):
            self.err(where, "승인 기록(approval) 없음. " + hint)
            return

        def said(value, name):
            if not isinstance(value, str) or len(value.strip()) < 2 or PLACEHOLDER.search(value.strip()):
                self.err(where, f"{name}: 사용자의 답을 그대로 적는다 (비었거나 자리표시 문구)")
                return False
            return True

        answers = ap.get("answers")
        if not isinstance(answers, dict):
            self.err(where, f"answers 없음: {', '.join(f'{k}({v})' for k, v in APPROVAL_KEYS.items())}. " + hint)
            answers = {}
        for key, name in APPROVAL_KEYS.items():
            if key not in answers:
                self.err(where, f"answers.{key} 없음 — {name}에 대한 사용자 답")
            else:
                said(answers[key], f"answers.{key} ({name})")
        said(ap.get("plan_ok"), "plan_ok (TOPIC 구성안을 승인한 사용자의 말)")
        approved = ap.get("plan")
        current = [f'{p.get("no")} {p.get("title")}' for p in plan]
        if not isinstance(approved, list) or not approved:
            self.err(where, "plan 없음 — 사용자가 승인한 구성안을 '01 제목' 형식 목록으로 그대로 적는다")
        elif [str(x).strip() for x in approved] != current:
            changed = [c for c in current if c not in approved] + [f"(삭제) {a}" for a in approved if a not in current]
            self.err(where, "승인한 구성안과 지금 plan 이 다르다: " + "; ".join(changed[:4])
                     + ". 바뀐 표를 사용자에게 다시 보여 주고 승인받아 approval.plan·plan_ok 를 갱신한다")
        if self.lenient and not (isinstance(ap.get("lenient"), str) and ap["lenient"].strip()):
            self.err(where, "--lenient 를 쓰려면 분량 규칙 완화를 허락한 사용자의 말을 approval.lenient 에 적는다")

    def check_problem_counts(self, d, built, scope):
        if self.p1:
            for k, name in (("warmup", "워밍업 문제(W)"), ("exam", "실전 문제(X)")):
                if d.get(k):
                    self.err(k, f"Part1 에는 {name}를 넣지 않는다")
            A, B = len(d.get("apply") or []), len(d.get("exercises") or [])
            if A < 1:
                self.err("apply", "확인문제(A)가 없음: 원서 Exercise 를 넣는다")
            if scope == "chapter":
                if B < 4:
                    self.count("exercises", f"연습문제(B)는 장 전체에서 4개 이상 ({B}개)")
                covered = {str(q.get("topic")) for q in (d.get("apply") or []) + (d.get("exercises") or [])}
                for no in built:
                    if no not in covered:
                        self.count(f"TOPIC {no}", "이 TOPIC 을 쓰는 확인문제(A)·연습문제(B)가 없음")
            return
        W, A, B, X = (len(d.get(k) or []) for k in ("warmup", "apply", "exercises", "exam"))
        if W < 1:
            self.err("warmup", "워밍업 문제(W)가 없음. 강의에서 다룬 원서 예제·문제를 [준비] 칸과 함께 넣는다")
        if A < 1:
            self.err("apply", "적용문제(A)가 없음")
        if scope == "chapter":
            if W < 2:
                self.count("warmup", f"워밍업 문제는 2개 이상 ({W}개)")
            if B < 4:
                self.count("exercises", f"연습문제(B)는 장 전체에서 4개 이상 ({B}개)")
            if X < 5:
                self.count("exam", f"실전 문제(X)는 장마다 5개 ({X}개): 시험 형식 그대로(T/F·단답 → 손추적 → 손코딩 등)")
            covered = {str(q.get("topic")) for q in (d.get("apply") or [])}
            for no in built:
                if no not in covered:
                    self.count(f"TOPIC {no}", "이 TOPIC 을 쓰는 적용문제(A)가 없음")
        elif A < 2:
            self.count("apply", f"시안에도 적용문제는 2개 이상 ({A}개)")


def chapter_body(page):
    """한 장의 HTML 에서 <body> 안쪽만. 여러 장을 한 책으로 이을 때 둘째 장부터 쓴다."""
    m = re.search(r"<body\b[^>]*>\n?(.*)</body>", page, re.S)
    inner = m.group(1) if m else page
    inner = inner.replace("<!-- FRONTMATTER -->\n", "", 1)
    return re.sub(r"<!-- tensor build.py 가 만든 파일[^\n]*-->\n", "", inner)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("json", type=Path, nargs="+", help="장 원고 JSON. 여러 개면 순서대로 한 책(book.html)으로 잇는다")
    ap.add_argument("-o", "--output", type=Path, help="기본: 첫 원고와 같은 폴더의 book.html")
    ap.add_argument("--lenient", action="store_true", help="분량 규칙을 경고로 낮춘다 (approval.lenient 에 사용자 허락이 있을 때만)")
    ap.add_argument("--color", action="store_true", help="컬러판(화면용): theme-mono 제거, fig/ → figc/ 강조색 그림")
    ap.add_argument("--accent", default="#6B3FD4", help="컬러판 그림 강조색")
    a = ap.parse_args()
    out = a.output or a.json[0].with_name("book.html")
    pages, errors, n_topics, n_problems = [], 0, 0, 0
    for path in a.json:
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"[오류] {path.name}: JSON 을 읽을 수 없음: {e}")
            errors += 1
            continue
        b = Builder(data, out.parent.resolve(), a.lenient)
        page = b.build()
        tag = f"{path.name} · " if len(a.json) > 1 else ""
        for line in b.warnings + b.errors:
            print(tag + line)
        errors += len(b.errors)
        n_topics += len(data.get("topics") or [])
        n_problems += len(b.labels)
        pages.append(page)
    if errors:
        print(f"\n오류 {errors}개 · 파일을 쓰지 않았다. JSON 원고를 고친 뒤 다시 실행한다.")
        sys.exit(1)
    page = pages[0]
    if len(pages) > 1:
        rest = "\n".join(chapter_body(p) for p in pages[1:])
        page = page.replace("</body></html>", rest + "\n</body></html>", 1)
    page = prep.expand_arrays(page)
    if a.color:
        page = re.sub(r'<link rel="stylesheet" href="[^"]*theme-mono\.css">\n?', "", page)
        page = page.replace('src="fig/', 'src="figc/')
        if (out.parent / "fig").is_dir():
            prep.colorize_figs(out.parent / "fig", out.parent / "figc", a.accent)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(stamp.seal(page), encoding="utf-8", newline="\n")
    chapters = f"{len(pages)}개 장 · " if len(pages) > 1 else ""
    print(f"{out} · {chapters}TOPIC {n_topics}개 · 문제 {n_problems}개 · 도장 찍음")


if __name__ == "__main__":
    main()
