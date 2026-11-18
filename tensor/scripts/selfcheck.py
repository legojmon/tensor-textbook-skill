"""Render the shared demo and compare each page against frozen grayscale images."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

from render import BUILD

import pymupdf
from PIL import Image, ImageChops

SKILL = Path(__file__).resolve().parents[1]
REF = SKILL / "selfcheck" / "ref"
DPI = 72


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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, help="이미 조판한 견본 PDF를 바로 대조")
    args = parser.parse_args()
    if args.pdf:
        compare(args.pdf, REF)
        return
    demo = SKILL.parent / "examples" / "demo" / "demo.html"
    if not demo.is_file():
        demo = SKILL / "selfcheck" / "demo" / "demo.html"
    if not demo.is_file():
        raise SystemExit("원본 저장소 또는 배포본의 견본 HTML과 fig/ 폴더가 필요합니다.")
    BUILD.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=BUILD, prefix="selfcheck-") as tmp:
        pdf = Path(tmp) / "demo.pdf"
        subprocess.run([sys.executable, str(SKILL / "scripts/render.py"),
                        str(demo), "-o", str(pdf), "--strict"], check=True)
        compare(pdf, REF)


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        sys.exit(str(error))
