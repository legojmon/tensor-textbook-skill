"""Render a TENSOR manuscript and optional page previews with the shared Chromium driver.

Only manuscripts made by build.py (and frontmatter.py) are accepted: the build stamp must match.
"""
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import argparse
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import tempfile

SKILL = Path(__file__).resolve().parents[1]
BUILD = Path(os.environ.get("TENSOR_BUILD", SKILL / ".build")).resolve()


def find_chrome():
    candidates = (os.environ.get("TENSOR_CHROME"), shutil.which("google-chrome"), shutil.which("chromium"),
                  shutil.which("chromium-browser"), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                  "C:/Program Files/Google/Chrome/Application/chrome.exe")
    return next((str(p) for p in candidates if p and Path(p).is_file()), None)


def resolve(html):
    modules = BUILD / "node_modules"
    resources = {"css": SKILL / "assets", "katex": modules / "katex/dist",
                 "pretendard": modules / "pretendard/dist/web/static", "serif": modules / "@fontsource/noto-serif-kr"}
    from matplotlib import get_data_path
    symbols = (Path(get_data_path()) / "fonts/ttf/STIXGeneral.ttf").as_uri()
    html = html.replace("</head>", f'<style>@font-face{{font-family:TensorSymbols;src:url("{symbols}")}}</style></head>', 1)
    if "tensor://serif/" not in html:
        links = "".join(f'<link rel="stylesheet" href="tensor://serif/{weight}.css">' for weight in (400, 700))
        # fontsource 는 한글을 120여 조각(unicode-range)으로 나눈다. 그대로 쓰면 PDF 에 글꼴이 조각마다 따로 들어가
        # 한 글자마다 글자 객체가 새로 생기고(쪽당 700개 안팎), 아이패드·맥에서 쪽이 늦게 뜬다.
        # 한글 11,172자와 기본 라틴을 한 파일에 담은 korean 조각을 범위 없이 마지막에 선언해 먼저 쓰게 한다.
        # 한자 등 그 밖의 글자만 위의 조각 파일로 넘어간다.
        whole = "".join(f'@font-face{{font-family:"Noto Serif KR";font-weight:{w};font-style:normal;'
                        f'src:url("tensor://serif/files/noto-serif-kr-korean-{w}-normal.woff2") format("woff2")}}'
                        for w in (400, 700))
        html = html.replace("</head>", links + f"<style>{whole}</style>" + "</head>", 1)
    for prefix, directory in resources.items():
        html = html.replace(f"tensor://{prefix}/", directory.as_uri() + "/")
    return html


def pin_sans(html):
    # Pretendard's upstream CSS prefers a locally installed font. Embed the locked files first.
    directory = (BUILD / "node_modules/pretendard/dist/web/static").as_uri()
    weights = ["Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black"]
    faces = "".join(f'@font-face{{font-family:Pretendard;font-weight:{i*100};src:url("{directory}/woff2/Pretendard-{name}.woff2")}}'
                    for i, name in enumerate(weights, 1))
    return re.sub(r'<link\b[^>]*href=["\'][^"\']*/pretendard\.css["\'][^>]*>', lambda _: f"<style>{faces}</style>",
                  html, flags=re.IGNORECASE)


def print_sheets(inputs, strict=True):
    """Each input is (HTML string, base directory for relative assets, PDF path, is manuscript)."""
    if not (BUILD / "node_modules/playwright-core/package.json").is_file():
        raise SystemExit("조판 환경 준비가 필요합니다. python tensor/scripts/setup.py")
    temporary = []
    sheets = []
    try:
        for html, directory, output, body in inputs:
            with tempfile.NamedTemporaryFile(dir=directory, prefix=".tensor-", suffix=".resolved.html",
                                             delete=False, mode="w", encoding="utf-8") as src:
                temporary.append(Path(src.name))
                src.write(pin_sans(html))
            sheets.append({"html": str(temporary[-1].resolve()), "pdf": str(output.resolve()), "body": body})
        job = {"sheets": sheets, "strict": strict, "build": str(BUILD), "systemChrome": find_chrome()}
        node = shutil.which("node")
        if not node:
            raise SystemExit("Node.js를 찾을 수 없습니다.")
        subprocess.run([node, str(SKILL / "scripts/print.cjs")], input=json.dumps(job).encode(), check=True,
                       timeout=max(120, 75 * len(sheets)))
    finally:
        for filename in temporary:
            filename.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--png", type=Path)
    parser.add_argument("--dpi", type=int, default=80)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--raw", action="store_true", help="마지막 가볍게 다시 쓰기(optimize.py)를 건너뛴다")
    args = parser.parse_args()
    output = args.output or args.html.with_suffix(".pdf")
    source = args.html.read_text(encoding="utf-8")
    import stamp
    ok, why = stamp.verify(source)
    if not ok:
        raise SystemExit(f"[조판 거부] {args.html.name}: {why}")
    print_sheets([(resolve(source), args.html.parent, output, True)], args.strict)
    if not args.raw:
        # 마지막 단계: 크롬이 한 자씩 찍은 글자를 원서처럼 줄 단위로 묶고 선형화한다(보기에는 같은 쪽).
        import optimize
        try:
            print(optimize.optimize(output))
        except ValueError as e:
            print(f"[경고] 가볍게 다시 쓰기 생략: {e}")
    if args.png:
        import pymupdf
        args.png.mkdir(parents=True, exist_ok=True)
        with pymupdf.open(output) as doc:
            for number, page in enumerate(doc, 1):
                page.get_pixmap(dpi=args.dpi).save(args.png / f"p{number:03d}.png")


if __name__ == "__main__":
    main()
