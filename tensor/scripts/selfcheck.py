"""Build the shared demo from its JSON manuscript, render it, and compare each page against frozen grayscale images."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from render import BUILD

import pymupdf
from PIL import Image, ImageChops

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SKILL = Path(__file__).resolve().parents[1]
REF = SKILL / "selfcheck" / "ref"
MANUSCRIPT = SKILL / "references" / "example-manuscript.json"
DPI = 72


def demo_figures():
    for candidate in (SKILL.parent / "examples" / "demo" / "fig", SKILL / "selfcheck" / "demo" / "fig"):
        if candidate.is_dir():
            return candidate
    raise SystemExit("견본 그림 폴더(examples/demo/fig 또는 selfcheck/demo/fig)가 필요합니다.")


def compare(pdf_path, reference):
    expected = sorted(reference.glob("p*.png"))
    if not expected:
        raise ValueError(f"기준 이미지가 없습니다: {reference}")
    with pymupdf.open(pdf_path) as doc:
        if len(doc) != len(expected):
            raise ValueError(f"쪽수 차이: 기준 {len(expected)}, 출력 {len(doc)}")
        errors = []
        for pg, path in zip(doc, expected):
            pix = pg.get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY, alpha=False)
            actual = Image.frombytes("L", (pix.width, pix.height), pix.samples)
            with Image.open(path) as img:
                baseline = img.convert("L")
            if actual.size != baseline.size:
                raise ValueError(f"{pg.number + 1}쪽 용지 크기가 기준과 다릅니다.")
            hist = ImageChops.difference(baseline, actual).histogram()
            ratio = sum(hist[17:]) / (pix.width * pix.height)
            print(f"{pg.number + 1:02}쪽  {ratio:.3%}")
            if ratio > 0.02:
                errors.append(pg.number + 1)
        if errors:
            raise ValueError(f"2% 초과 페이지: {errors}")
        print(f"통과 · {len(doc)}쪽, 각 쪽의 허용 차이 2%")


def build_demo(directory):
    """JSON 견본 → HTML → PDF. 빌더와 렌더러를 함께 검증한다."""
    shutil.copytree(demo_figures(), directory / "fig")
    html = directory / "demo.html"
    subprocess.run([sys.executable, str(SKILL / "scripts/build.py"), str(MANUSCRIPT), "-o", str(html)], check=True)
    subprocess.run([sys.executable, str(SKILL / "scripts/lint.py"), str(html), "--draft"], check=True)
    pdf = directory / "demo.pdf"
    subprocess.run([sys.executable, str(SKILL / "scripts/render.py"), str(html), "-o", str(pdf), "--strict"], check=True)
    return html, pdf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, help="이미 조판한 견본 PDF를 바로 대조")
    args = parser.parse_args()
    if args.pdf:
        compare(args.pdf, REF)
        return
    BUILD.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=BUILD, prefix="selfcheck-") as tmp:
        _, pdf = build_demo(Path(tmp))
        compare(pdf, REF)


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        sys.exit(str(error))
