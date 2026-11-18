#!/usr/bin/env python3
"""Tensor 원고 점검기 — 구조·문체·번호·수식 규칙 위반을 찾는다.

    python lint.py work/book.html [--inventory work/INVENTORY.md] [--draft]

build.py 가 만든 book.html 을 다시 검사한다(손으로 고친 흔적, 문체, 번호 대조).
경고 0개가 될 때까지 JSON 원고를 고치고 build.py 를 다시 돌린다. --draft 는 TOPIC 시안용
(TOPIC 수·연습문제 B 를 묻지 않는다).
"""
import argparse
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BS = chr(92)
BANNED = ["진심으로", "환영합니다", "무기로", "무기를", "여정", "사고가 확장", "경험을 하게 될", "꿀팁", "치트키",
          "놀랍게도", "인 것 같다", "아마도", "완벽하게", "탄탄한", "차근차근", "함께 해", "여러분"]
POLITE = re.compile(r"(습니다|십시오|세요|해요|이에요|예요|입니다)[.\s<]")
ABSOLUTE = re.compile(r"(항상|언제나|늘 |무조건|모든 경우)")
DASH = re.compile(r"\s[—–]\s|[가-힣a-zA-Z)]—|—[가-힣]")
# 원서 번호: Example 14.7-1 / P14.8-3 / Exercise 5.3 / Listing 5.3 / R-8.3 / C-8.12 / Figure 10.4
ID = re.compile(r"(?:Example|Exercise|Problem|Listing|Figure|Practice|Ex|P|R|C)[-\s]?(\d{1,2}[.\-]\d{1,3}(?:-\d{1,3})?)\b")
PARTS = [(".sol:not(.exam)", "원서적 해법"), (".sol.exam", "시험적 해법"), (".bubble", "말풍선"), (".concept", "시험 개념 박스"),
         (".core", "CORE"), (".grade", "채점 포인트"), (".vs", "강의 VS 연습문제 표"), (".ex", "EX"), ("h3", "소절 제목")]
PAGES = [("section.page.cover", "장 표지"), ("section.page.toc", "장 목차"), ("[data-id=preview]", "Preview"),
         ("[data-id=review]", "Review: 개념진단"), ("section.topic[data-no='해설']", "빠른 정답·해설")]


def text_of(el):
    return re.sub(r"\s+", " ", el.get_text(" ")).strip()


def structure(soup, W, draft):
    def warn(where, msg):
        W.append(f"[구조] {where}: {msg}")
    if soup.find("style"):
        warn("문서", "원고 안의 <style> — 조판은 tensor.css 만 쓴다. build.py 로 다시 만든다")
    for el in soup.find_all(style=True):
        if el.name != "img":
            warn(text_of(el)[:24] or el.name, "style 속성 — 고정 부품 밖 조판 금지. JSON 원고와 build.py 로 만든다")
            break
    for sel, name in PAGES:
        if not soup.select_one(sel):
            warn("쪽", f"{name} 쪽 없음")
    for pg in soup.select("section.page"):
        cls = pg.get("class", [])
        if "cover" in cls or "toc" in cls or pg.get("data-id") or pg.get("data-run") or pg.get("data-front"):
            continue
        warn("쪽", f"정체불명의 고정 쪽: {text_of(pg)[:30]}")
    topics = [t for t in soup.select("section.topic") if t.get("data-no", "").isdigit()]
    if not topics:
        warn("본문", "TOPIC(section.topic)이 하나도 없음 — 원고가 비었다")
    elif not draft and len(topics) < 6:
        warn("본문", f"TOPIC {len(topics)}개 — 장 전체는 6~12개 (시안이면 --draft)")
    seen = set()
    for t in topics:
        no = t.get("data-no", "?")
        if no in seen:
            warn(f"TOPIC {no}", "번호 중복")
        seen.add(no)
        if not t.get("data-title"):
            warn(f"TOPIC {no}", "제목(data-title) 없음")
        for sel, name in PARTS:
            if not t.select(sel):
                warn(f"TOPIC {no}", f"{name} 없음")
        for i, ex in enumerate(t.select(".ex"), 1):
            badge = ex.select_one(".badge")
            num = badge.select_one("span").get_text(strip=True) if badge and badge.select_one("span") else ""
            if not badge or badge.get_text(strip=True) != f"EX{num}" or num != f"{i:02d}":
                warn(f"TOPIC {no} EX {i}", f"EX 번호 형식 (EX {i:02d} 이어야 함)")
            if not ex.select_one(".src") or not text_of(ex.select_one(".src")).strip("[] "):
                warn(f"TOPIC {no} EX {i:02d}", "출처(.src) 없음")
            if not ex.select_one(".txt.q") or len(text_of(ex.select_one(".txt.q"))) < 10:
                warn(f"TOPIC {no} EX {i:02d}", "지문 없음")
        for c in t.select(".concept"):
            cls = c.get("class", [])
            if "book" in cls or "ind" in cls:
                continue
            if not c.select(".cond"):
                warn(f"TOPIC {no}", f"시험 개념 박스 '{text_of(c.select_one('.ttl') or c)[:16]}' 에 적용 조건(.cond) 없음")
            if not c.select(".tabs .on"):
                warn(f"TOPIC {no}", "개념 박스의 3탭 중 선택된 탭(.on) 없음")
        for s_ in t.select(".sol.exam"):
            if s_.select_one(".lab") and not s_.select(".cond"):
                warn(f"TOPIC {no}", "시험적 해법에 적용 조건(.cond) 없음")
    sections = {s.get("data-id"): s for s in soup.select("section.problems")}
    for pid, prefix, name in [("warmup", "W", "워밍업 문제"), ("a01", "A", "TOPIC 적용문제"), ("b01", "B", "연습문제"), ("exam", "X", "실전 문제")]:
        sec = sections.get(pid)
        if sec is None:
            if pid not in ("b01", "exam") or not draft:
                warn("문제", f"{name}({prefix}) 쪽 없음")
            continue
        items = sec.select(":scope > .qitem")
        if not items:
            warn("문제", f"{name} 쪽에 문제가 없음 (빈 문제 쪽)")
        for i, q in enumerate(items, 1):
            label = q.get("data-no", "")
            if label != f"{prefix}·{i:02d}":
                warn(name, f"번호 '{label}' — {prefix}·{i:02d} 이어야 함 (L·A·B 만 쓴다)")
            if not q.get("data-src"):
                warn(label or f"{prefix} {i}", "출처(data-src) 없음")
            if not q.get("data-hint"):
                warn(label or f"{prefix} {i}", "힌트(data-hint) 없음")
            if not q.get("data-topic"):
                warn(label or f"{prefix} {i}", "관련 TOPIC(data-topic) 없음")
            if not q.select_one(".t") or len(text_of(q.select_one(".t"))) < 10:
                warn(label, "지문 없음")
            if pid == "warmup" and not q.select_one(".t > .pre"):
                warn(label, "워밍업 문제의 [준비] 칸(pre) 없음")
    ans = soup.select_one("section.topic[data-no='해설']")
    if ans is not None:
        got = text_of(ans)
        for q in soup.select(".qitem"):
            lb = q.get("data-no", "")
            if lb and lb not in got:
                warn("빠른 정답·해설", f"{lb} 의 답이 없음")


def style(soup, W):
    def warn(kind, where, msg):
        W.append(f"[{kind}] {where}: {msg}")
    # 코드와 빠른 정답·해설 장은 문체 검사에서 뺀다
    for t in soup.select("pre.code, section.topic[data-no='해설']"):
        t.decompose()
    for t in soup.select("code.c"):
        t.replace_with("CODE")
    prose = soup.select("p, .step, .box, .body, .tip .body, .grade .body, .pv-box, .note, .t, li, .hint, .cond, .core .box, h3")
    for el in prose:
        tx = text_of(el)
        where = (tx[:28] + "…") if len(tx) > 28 else tx
        for b in BANNED:
            if b in tx:
                warn("문체", where, f"금지 표현 '{b}'")
        if POLITE.search(tx + " ") and not el.find_parent(class_="back-cover"):
            warn("문체", where, "존댓말 — 책 전체 평서문(~이다)")
        if DASH.search(tx) and not el.find_parent("table"):
            warn("문체", where, "대시(—)로 문장 잇기 — 쉼표·마침표로")
        if "!" in re.sub(r"\$[^$]*\$", "", tx) and not el.find_parent(class_="bubble"):
            warn("문체", where, "느낌표")
        if tx.count("$") % 2:
            warn("수식", where, "$ 짝이 맞지 않음")
        for m in re.finditer(r"(?<!\$)\$(?!\$)([^$]*)\$", tx):
            if BS + "dfrac" in m.group(1):
                warn("수식", where, "인라인 수식에 " + BS + "dfrac — " + BS + "tfrac 또는 a/b")
        if re.search("(" + BS + r"therefore|∴)[^$]*?=\s*-?[\d.]+\s*\$*\s*$", tx):
            warn("수식", where, "결과에 단위가 없는 것 같음")
    for el in soup.select("h3, .core .box, .concept .ttl, td"):
        if ABSOLUTE.search(text_of(el)):
            warn("일반화", text_of(el)[:30], "'항상/늘/모든' — 원서 정리로 증명된 게 아니면 조건을 붙인다")
    for sec in soup.select("section.topic"):
        if ABSOLUTE.search(sec.get("data-title", "")):
            warn("일반화", sec.get("data-title"), "TOPIC 제목의 절대 표현")
    for q in soup.select(".qitem .t, .ex .txt.q"):
        tx = text_of(q)
        if not re.search(r"(하시오|구하시오|쓰시오|보이시오|설명하시오|답하시오|정하시오|밝히시오|T/F|참/거짓|\?)[.\s)]*$", tx):
            warn("문체", tx[:28] + "…", "문제 지문은 '~하시오/~구하시오'로 끝낸다")


def numbers(soup, inventory, W):
    inv = Path(inventory).read_text(encoding="utf-8")
    known = {m.group(1) for m in ID.finditer(inv)}
    known |= set(re.findall(r"(\d{1,2}\.\d{1,2}-\d{1,3})\(p\.", inv))
    full = soup.get_text(" ") + " ".join(q.get("data-src", "") for q in soup.select(".qitem"))
    for m in ID.finditer(full):
        num = m.group(1)
        if "-" not in num and re.match(r"\d+\.\d{2,}$", num):
            W.append(f"[번호] {m.group(0)}: 하이픈 빠진 번호 같음 (예: 14.83 → 14.8-3)")
        elif known and num not in known:
            W.append(f"[번호] {m.group(0)}: INVENTORY 에 없는 원서 번호 — 오타, 다른 장, 또는 보조 교재의 장 번호")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html")
    ap.add_argument("--inventory")
    ap.add_argument("--draft", action="store_true", help="TOPIC 시안: TOPIC 수와 연습문제(B)를 묻지 않는다")
    a = ap.parse_args()
    soup = BeautifulSoup(Path(a.html).read_text(encoding="utf-8"), "html.parser")
    W = []
    structure(soup, W, a.draft)
    for t in soup(["script", "style"]):
        t.decompose()
    style(soup, W)
    if a.inventory:
        numbers(soup, a.inventory, W)
    for w in W:
        print(w)
    print(f"\n경고 {len(W)}개" if W else "경고 없음")
    sys.exit(1 if W else 0)


if __name__ == "__main__":
    main()
