"""Build or replace the opening pages of a TENSOR manuscript."""
import argparse
from html import escape
import json
import os
from pathlib import Path
import re
from tempfile import NamedTemporaryFile

START = "<!-- FRONTMATTER -->"
END = "<!-- /FRONTMATTER -->"


def txt(value):
    return escape(str(value or ""))


def paragraphs(values):
    if isinstance(values, str):
        values = values.splitlines()
    return "".join(f"<p>{txt(value)}</p>" for value in values if value)


def photo(base, value, css):
    if not value:
        return ""
    path = (base / value).resolve()
    if not path.is_file():
        raise ValueError(f"저자 이미지 파일을 찾을 수 없습니다: {path}")
    return f'<img class="{css}" src="{txt(path.as_uri())}" alt="">'


def section(title, items, extra=""):
    blocks = "".join(items)
    if not blocks:
        return ""
    return (f'<section class="page fm nofoot {extra}" data-front="1">'
            f'<h1>{txt(title)}</h1><div class="fm-body">{blocks}</div></section>\n')


def entry(label, detail=""):
    if not label and not detail:
        return ""
    return f'<div class="fm-entry"><b>{txt(label)}</b>{paragraphs(detail)}</div>'


def render(authors, book, base):
    people = [p for p in authors.get("authors", []) if p.get("name")]
    pages = [section(f'{authors.get("brand", "TENSOR")} 시리즈', (
        entry(s["subject"], " · ".join([*s.get("parts", []), s.get("status", "")]).strip(" ·"))
        for s in authors.get("series", []) if s.get("subject")))]
    timeline = [entry(s.get("label"), s.get("date", "")) for s in book.get("semester", [])]
    timeline.extend(entry(s.get("when"), s.get("what", "")) for s in book.get("roadmap_steps", []))
    pages.append(section("학기 로드맵", timeline))
    pages.append(section("TENSOR에 대하여", (entry(x.get("title"), x.get("text", ""))
                                         for x in book.get("about", []))))
    preface = paragraphs(book.get("preface", [])) + paragraphs(book.get("thanks", ""))
    if preface:
        signatures = "".join(photo(base, p.get("signature"), "fm-sign") for p in people)
        note = book.get("preface_note")
        caption = f'<p class="fm-note">{txt(note)}</p>' if note else ""
        pages.append(section("서문", [preface, caption, signatures]))
    profiles = []
    for person in people:
        portrait = photo(base, person.get("photo"), "fm-photo")
        profiles.append(f'<div class="fm-profile">{portrait}<div><h2>{txt(person["name"])}</h2>'
                        f'<small>{txt(person.get("name_en"))}</small>{paragraphs(person.get("bio", []))}'
                        f'{paragraphs(person.get("message", ""))}</div></div>')
    pages.append(section("저자 소개", profiles))
    pages.append(section("이 책의 구성", [
        '<p><span class="tg ws">원서 개념</span> 정의와 성립 근거를 먼저 읽는다.</p>',
        '<p><span class="tg">시험 개념</span> 문제에서 반복되는 관찰과 적용 조건을 확인한다.</p>',
        '<p><span class="tg ind">간접 개념</span> 풀이에 필요한 관련 개념을 짚는다.</p>',
        entry("예제와 해법", "원서적 해법에서 출발해 시험적 해법을 비교하고 채점 포인트를 확인한다."),
        entry("문제와 Review", "워밍업 문제로 시작해 적용문제·연습문제·실전 문제를 풀고 Review에서 놓친 조건을 확인한다.")]))
    pages.append(section("독자 수기", (entry(x["name"], x["text"]) for x in book.get("testimonials", [])
                                    if x.get("consent") is True and x.get("text") and x.get("name"))))
    pages.append(section("소통", (entry(k, v) for k, v in authors.get("contact", {}).items() if v)))
    pages.append(section("판권", (entry(k, v) for k, v in book.get("colophon", {}).items() if v)))
    pages.append(section("전체 차례", ['<div class="fm-toc"></div>'], "book-toc"))
    part = book.get("part") or {}
    if part.get("title") or part.get("name"):
        pages.append(section(part.get("name", ""), [f'<h2>{txt(part.get("title"))}</h2>'], "fm-part"))
        guide = [entry("목표", part["goals"])] if part.get("goals") else []
        guide.extend(entry("□ " + x) for x in part.get("checklist", []) if x)
        pages.append(section("Part 가이드라인", guide))
    return "".join(pages)


def insert(source, pages):
    block = START + "\n" + pages + END
    if START in source:
        if source.count(START) != 1 or source.count(END) > 1:
            raise ValueError("앞부분 삽입 표식이 중복되었습니다.")
        start = source.index(START)
        end = source.index(END, start) + len(END) if END in source else start + len(START)
        return source[:start] + block + source[end:]
    body = re.search(r"<body\b[^>]*>", source, re.IGNORECASE)
    if not body:
        raise ValueError("원고에서 body 태그를 찾을 수 없습니다.")
    return source[:body.end()] + "\n" + block + source[body.end():]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authors", required=True, type=Path)
    parser.add_argument("--book", required=True, type=Path)
    parser.add_argument("--into", required=True, type=Path)
    args = parser.parse_args()
    load = lambda path: json.loads(path.read_text(encoding="utf-8-sig"))
    pages = render(load(args.authors), load(args.book), args.authors.parent)
    result = insert(args.into.read_text(encoding="utf-8"), pages)
    with NamedTemporaryFile(mode="w", dir=args.into.parent, encoding="utf-8",
                            newline="\n", delete=False) as tmp:
        tmp.write(result)
    try:
        os.replace(tmp.name, args.into)
    finally:
        Path(tmp.name).unlink(missing_ok=True)
    print(f"앞부분 {pages.count('data-front=')}쪽 구성 · {args.into}")


if __name__ == "__main__":
    main()
