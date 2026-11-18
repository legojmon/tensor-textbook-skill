#!/usr/bin/env python3
"""Tensor 원고 점검기 — 문체·구조·번호·수식 규칙 위반을 찾는다.

    python3 lint.py work/book.html [--inventory work/INVENTORY.md]

경고 0개가 될 때까지 고친다. (writing-style.md 의 규칙을 기계적으로 확인할 수 있는 것만 잡는다)
"""
import argparse, re, sys
from pathlib import Path
from bs4 import BeautifulSoup

BANNED = ["진심으로", "환영합니다", "무기로", "무기를", "여정", "사고가 확장", "경험을 하게 될", "꿀팁", "치트키",
          "놀랍게도", "인 것 같다", "아마도", "완벽하게", "탄탄한", "차근차근", "함께 해", "여러분"]
POLITE = re.compile(r"(습니다|십시오|세요|해요|이에요|예요|입니다)[.\s<]")
ABSOLUTE = re.compile(r"(항상|언제나|늘 |무조건|모든 경우)")
DASH = re.compile(r"\s[—–]\s|[가-힣a-zA-Z)]—|—[가-힣]")
ID = re.compile(r"(?:Example|Exercise|Problem|P)\s?(\d{1,2}\.\d{1,2}(?:-\d{1,3})?)")


def text_of(el):
    return re.sub(r"\s+", " ", el.get_text(" ")).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--inventory")
    a = ap.parse_args()
    soup = BeautifulSoup(Path(a.html).read_text(encoding="utf-8"), "html.parser")
    for t in soup(["script", "style"]):
        t.decompose()
    W = []

    def warn(kind, where, msg):
        W.append(f"[{kind}] {where}: {msg}")

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
            if "\\dfrac" in m.group(1):
                warn("수식", where, "인라인 수식에 \\dfrac — \\tfrac 또는 a/b")
        if re.search(r"(\\therefore|∴)[^$]*?=\s*-?[\d.]+\s*\$*\s*$", tx):
            warn("수식", where, "결과에 단위가 없는 것 같음")
    for el in soup.select("h3, .core .box, .topic, .concept .ttl, td"):
        tx = text_of(el) if el.name != "section" else el.get("data-title", "")
        if ABSOLUTE.search(tx):
            warn("일반화", tx[:30], "'항상/늘/모든' — 원서 정리로 증명된 게 아니면 조건을 붙인다")
    for sec in soup.select("section.topic"):
        if ABSOLUTE.search(sec.get("data-title", "")):
            warn("일반화", sec.get("data-title"), "TOPIC 제목의 절대 표현")
    # 구조: 시험 개념 박스·시험적 해법의 적용 조건
    for c in soup.select(".concept"):
        cls = c.get("class", [])
        if "book" in cls or "ind" in cls:
            continue
        if not c.select(".cond"):
            warn("구조", text_of(c.select_one(".ttl") or c)[:24], "시험 개념 박스에 적용 조건(.cond) 없음")
    for s_ in soup.select(".sol.exam"):
        if not s_.select(".cond") and s_.select_one(".lab"):
            warn("구조", text_of(s_)[:24], "시험적 해법에 적용 조건(.cond) 없음")
    for t in soup.select("section.topic"):
        no = t.get("data-no")
        for need, name in [(".sol:not(.exam)", "원서적 해법"), (".sol.exam", "시험적 해법"), (".bubble", "말풍선"),
                           (".concept", "시험 개념 박스"), (".core", "CORE"), (".grade", "채점 포인트"), (".vs", "강의 VS 연습문제 표")]:
            if not t.select(need):
                warn("구조", f"TOPIC {no}", f"{name} 없음")
    for q in soup.select(".qitem"):
        if not q.get("data-src"):
            warn("문제", q.get("data-no", "?"), "출처(data-src) 없음")
        if not q.get("data-hint"):
            warn("문제", q.get("data-no", "?"), "힌트(data-hint) 없음")
    # 번호: INVENTORY 와 대조
    if a.inventory:
        inv = Path(a.inventory).read_text(encoding="utf-8")
        known = set(re.findall(r"(\d{1,2}\.\d{1,2}-\d{1,3})\(p\.", inv))
        full = soup.get_text(" ") + " ".join(q.get("data-src", "") for q in soup.select(".qitem"))
        for m in ID.finditer(full):
            num = m.group(1)
            if "-" not in num and re.match(r"\d+\.\d{2,}$", num):
                warn("번호", m.group(0), "하이픈 빠진 번호 같음 (예: 14.83 → 14.8-3)")
            elif "-" in num and known and num not in known:
                warn("번호", m.group(0), "INVENTORY 에 없는 원서 번호 — 오타 또는 다른 장")
    for w in W:
        print(w)
    print(f"\n경고 {len(W)}개" if W else "경고 없음")
    sys.exit(1 if W else 0)


if __name__ == "__main__":
    main()
