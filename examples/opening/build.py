"""Build the shared authors' opening and its matching back cover."""
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile

import pymupdf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCRIPTS = ROOT / "tensor/scripts"
DEMO = ROOT / "examples/demo"


def run(script, *args):
    subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], check=True)


def main():
    scratch = ROOT / "work"
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch, prefix="opening-") as directory:
        work = Path(directory)
        manuscript = work / "book.html"
        # 책 전체는 1쪽부터: 견본 JSON 의 시작 쪽만 바꿔 build.py 로 다시 만든다(HTML 은 손대지 않는다)
        source = json.loads((ROOT / "tensor/references/example-manuscript.json").read_text(encoding="utf-8"))
        source["start_page"] = 1
        (work / "book.json").write_text(json.dumps(source, ensure_ascii=False), encoding="utf-8")
        shutil.copytree(DEMO / "fig", work / "fig")
        run("build.py", work / "book.json", "-o", manuscript)
        run("frontmatter.py", "--authors", ROOT / "author/authors.json", "--book", HERE / "book.json", "--into", manuscript)
        run("render.py", manuscript, "-o", work / "book.pdf", "--strict")
        cover = json.loads((HERE / "cover.json").read_text(encoding="utf-8"))
        with pymupdf.open(work / "book.pdf") as document:
            cover["pages"] = len(document)
        config = work / "cover.json"
        config.write_text(json.dumps(cover, ensure_ascii=False), encoding="utf-8")
        run("cover.py", config, "-o", work / "cover")
        shutil.copyfile(work / "book.pdf", HERE / "book.pdf")
        shutil.copyfile(work / "cover/back.pdf", HERE / "back.pdf")


if __name__ == "__main__":
    main()
