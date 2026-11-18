#!/usr/bin/env python3
"""Tensor 입력 분석기 — 강의록 PDF + 원서 PDF(+ 해설집)를 읽어 작업 폴더를 만든다.

    python3 extract.py --lecture lec.pdf --textbook book.pdf [--solutions sol.pdf] \
                       [--chapter 14] [--pages 690-760] --out work/

만들어지는 것 (work/):
  INVENTORY.md            ← 가장 먼저 읽을 요약: 장 범위, 절 목록, 예제/연습/장끝문제 목록, 강의↔원서 대응표
  lecture/text.md         ← 강의록 쪽별 텍스트
  lecture/sheet_XX.png    ← 강의록 6쪽 모아보기 (수식·그림은 이걸 보고 읽는다)
  lecture/pNNN.png        ← 강의록 쪽 이미지
  textbook/text.md        ← 원서 해당 장 쪽별 텍스트
  textbook/pNNNN.png      ← 원서 해당 장 쪽 이미지 (그림 다시 그릴 때 본다)
  solutions/text.md       ← 해설집 해당 장 텍스트 (있으면)
  mapping.csv             ← 강의 쪽, 강의 표기, 원서 번호, 원서 쪽

스캔본(텍스트 없음)이면 경고를 내고 이미지만 만든다 — 이때는 이미지를 직접 보고 목록을 만든다.
"""
import argparse, csv, re, sys
from pathlib import Path

import pymupdf

ID = r"\d{1,2}\.\d{1,2}(?:-\d{1,3})?"
PAT = {
    "example":  re.compile(rf"(?i)\bexample\s+({ID})"),
    "exercise": re.compile(rf"(?i)\bexercise\s+({ID})"),
    "problem":  re.compile(rf"(?im)^\s*(?:P|Problem)\s?({ID})\b"),
    "figure":   re.compile(rf"(?i)\bfigure\s+(?:P\s?|E\s?)?({ID})"),
}
LECTURE_REF = re.compile(rf"(?i)\b(ex(?:ample)?|exercise|prob(?:lem)?|p)\.?\s*({ID})")


def page_text(doc, i):
    return doc[i].get_text()


def is_scanned(doc, pages):
    sample = [i for i in pages][: min(8, len(pages))]
    chars = sum(len(page_text(doc, i).strip()) for i in sample)
    return chars < 40 * max(1, len(sample))


def find_chapter_range(doc, ch):
    starts = []
    pat = re.compile(rf"(?i)^\s*chapter\s+{ch}\b")
    nxt = re.compile(rf"(?i)^\s*chapter\s+{ch + 1}\b")
    s = e = None
    for i in range(len(doc)):
        head = page_text(doc, i)[:120]
        if s is None and pat.search(head):
            # 목차 쪽 제외: 본문 장 첫 쪽은 보통 "IN THIS CHAPTER" 나 절 목록이 뒤따른다
            s = i
        elif s is not None and nxt.search(head):
            e = i - 1
            break
    if s is not None and e is None:
        e = min(len(doc) - 1, s + 90)
    # 목차의 "CHAPTER n" 을 잡았을 수 있으니, 그 쪽에 예제/문제가 하나도 없으면 다음 후보를 찾는다
    if s is not None:
        body = "".join(page_text(doc, i) for i in range(s, min(e + 1, s + 15)))
        if not PAT["example"].search(body) and not PAT["problem"].search(body):
            for i in range(s + 1, len(doc)):
                if pat.search(page_text(doc, i)[:120]):
                    return find_chapter_range_from(doc, ch, i)
    return s, e


def find_chapter_range_from(doc, ch, s):
    nxt = re.compile(rf"(?i)^\s*chapter\s+{ch + 1}\b")
    for i in range(s + 1, len(doc)):
        if nxt.search(page_text(doc, i)[:120]):
            return s, i - 1
    return s, min(len(doc) - 1, s + 90)


def guess_chapter(lec):
    t = "".join(page_text(lec, i) for i in range(min(3, len(lec))))
    m = re.search(r"(?i)\bch(?:apter)?\.?\s*(\d{1,2})\b", t)
    return int(m.group(1)) if m else None


def render(doc, i, path, dpi):
    doc[i].get_pixmap(dpi=dpi).save(path)


def sheets(paths, out_dir, prefix="sheet", per=6):
    from PIL import Image
    ims = [Image.open(p) for p in paths]
    if not ims:
        return []
    w, h = ims[0].size
    outs = []
    for k in range(0, len(ims), per):
        chunk = ims[k:k + per]
        sh = Image.new("RGB", (2 * w, 3 * h), "white")
        for j, im in enumerate(chunk):
            sh.paste(im.resize((w, h)), ((j % 2) * w, (j // 2) * h))
        p = out_dir / f"{prefix}_{k // per + 1:02d}.png"
        sh.save(p)
        outs.append(p)
    return outs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lecture", required=True)
    ap.add_argument("--textbook", required=True)
    ap.add_argument("--solutions")
    ap.add_argument("--chapter", type=int)
    ap.add_argument("--pages", help="원서 장 범위를 직접 지정 (1부터 세는 PDF 쪽, 예: 690-760)")
    ap.add_argument("--out", default="work")
    a = ap.parse_args()

    out = Path(a.out)
    (out / "lecture").mkdir(parents=True, exist_ok=True)
    (out / "textbook").mkdir(parents=True, exist_ok=True)
    lec = pymupdf.open(a.lecture)
    book = pymupdf.open(a.textbook)
    notes = []

    ch = a.chapter or guess_chapter(lec)
    if ch is None:
        sys.exit("장 번호를 찾지 못했습니다. --chapter 로 지정하세요.")

    # ---------------- lecture
    lec_pngs = []
    with open(out / "lecture/text.md", "w", encoding="utf-8") as f:
        for i in range(len(lec)):
            f.write(f"\n## 강의 p.{i + 1}\n{page_text(lec, i)}\n")
            p = out / f"lecture/p{i + 1:03d}.png"
            render(lec, i, p, 70)
            lec_pngs.append(p)
    lec_sheets = sheets(lec_pngs, out / "lecture")
    if is_scanned(lec, range(len(lec))):
        notes.append("강의록이 스캔본입니다 — lecture/sheet_*.png 를 직접 보고 읽으세요.")

    # ---------------- textbook chapter
    if a.pages:
        s, e = [int(x) - 1 for x in a.pages.split("-")]
    else:
        s, e = find_chapter_range(book, ch)
    if s is None:
        sys.exit(f"원서에서 CHAPTER {ch} 를 찾지 못했습니다. --pages 로 범위를 지정하세요.")
    scanned = is_scanned(book, range(s, e + 1))
    if scanned:
        notes.append("원서가 스캔본입니다 — textbook/p*.png 를 직접 보고 예제·문제 목록을 만드세요.")

    items = {k: {} for k in PAT}
    sections = []
    sec_pat = re.compile(rf"(?m)^\s*({ch}\.\d{{1,2}})\s*\n\s*([A-Z][^\n]{{2,70}})")
    with open(out / "textbook/text.md", "w", encoding="utf-8") as f:
        for i in range(s, e + 1):
            t = page_text(book, i)
            f.write(f"\n## 원서 PDF p.{i + 1}\n{t}\n")
            render(book, i, out / f"textbook/p{i + 1:04d}.png", 110)
            for k, pat in PAT.items():
                for m in pat.finditer(t):
                    if m.group(1).startswith(f"{ch}."):
                        items[k].setdefault(m.group(1), i + 1)
            for m in sec_pat.finditer(t):
                title = re.sub(r"\s+", " ", m.group(2)).strip()
                if m.group(1) not in [x[0] for x in sections]:
                    sections.append((m.group(1), title.replace(" ", "") if len(title.split()) > 6 else title, i + 1))

    # ---------------- solutions
    sol_idx = {}
    if a.solutions:
        (out / "solutions").mkdir(exist_ok=True)
        sol = pymupdf.open(a.solutions)
        with open(out / "solutions/text.md", "w", encoding="utf-8") as f:
            for i in range(len(sol)):
                t = page_text(sol, i)
                if re.match(rf"\s*{ch}-\d", t) or re.search(rf"(?i)chapter\s+{ch}\b", t[:200]):
                    f.write(f"\n## 해설 PDF p.{i + 1}\n{t}\n")
                    for m in re.finditer(rf"(?i)\b(?:P|Problem|Exercise|Example)\s?({ch}\.\d{{1,2}}-\d{{1,3}})", t):
                        sol_idx.setdefault(m.group(1), i + 1)

    # ---------------- lecture ↔ textbook mapping
    def where(num):
        for k in ("example", "exercise", "problem"):
            if num in items[k]:
                return k, items[k][num]
        return "", ""

    rows = []
    for i in range(len(lec)):
        for m in LECTURE_REF.finditer(page_text(lec, i)):
            num = m.group(2)
            if not num.startswith(f"{ch}."):
                continue
            kind, pg = where(num)
            key = (num, kind)
            if any(r[2] == num for r in rows):
                continue
            rows.append([i + 1, m.group(0).strip(), num, kind, pg, sol_idx.get(num, "")])
    with open(out / "mapping.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["강의 쪽", "강의 표기", "번호", "원서 종류", "원서 PDF 쪽", "해설 PDF 쪽"])
        w.writerows(rows)

    # ---------------- INVENTORY
    L = [f"# INVENTORY — Chapter {ch}\n"]
    L.append(f"- 강의록: {Path(a.lecture).name} ({len(lec)}쪽) → lecture/text.md, lecture/sheet_*.png ({len(lec_sheets)}장)")
    L.append(f"- 원서: {Path(a.textbook).name} — 이 장은 PDF p.{s + 1}–{e + 1} → textbook/text.md, textbook/p*.png")
    if a.solutions:
        L.append(f"- 해설집: {Path(a.solutions).name} → solutions/text.md (번호 {len(sol_idx)}개 색인)")
    for n in notes:
        L.append(f"- ⚠ {n}")
    L.append("\n## 절 목록")
    for num, title, pg in sections:
        L.append(f"- {num} {title} (p.{pg})")
    for k, label in [("example", "예제 Example"), ("exercise", "연습 Exercise"), ("problem", "장 끝 문제 Problems")]:
        L.append(f"\n## {label} — {len(items[k])}개")
        L.append(", ".join(f"{n}(p.{p})" for n, p in sorted(items[k].items(), key=lambda x: [int(y) for y in re.split(r'[.-]', x[0])])) or "(없음)")
    L.append("\n## 강의 ↔ 원서 대응 (mapping.csv)")
    L.append("| 강의 쪽 | 강의 표기 | 번호 | 원서 종류 | 원서 쪽 | 해설 쪽 |\n|---|---|---|---|---|---|")
    for r in rows:
        L.append("| " + " | ".join(str(x) for x in r) + " |")
    if not rows:
        L.append("(자동 대응 없음 — 강의 시트를 보고 원서 예제와 수치를 비교해 직접 대응시키세요)")
    L.append("\n## 다음 할 일\n1. 강의 시트(lecture/sheet_*.png)를 전부 본다. 대응표에 없는 강의 예제는 수치·그림으로 원서 예제를 찾아 대응시킨다.\n"
             "2. 장 끝 문제 목록을 훑으며 '결정적 관찰'을 적고 시험 개념 후보를 묶는다 (references/content-rules.md §3).\n"
             "3. 강의 뒤쪽에 채점 기준(배점·감점)이 있으면 표시해 둔다 → 채점 포인트 근거.")
    (out / "INVENTORY.md").write_text("\n".join(L), encoding="utf-8")
    print((out / "INVENTORY.md").read_text(encoding="utf-8")[:3000])


if __name__ == "__main__":
    main()
