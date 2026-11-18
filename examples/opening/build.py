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
        source = (DEMO / "demo.html").read_text(encoding="utf-8")
        manuscript.write_text(source.replace('data-start="16"', 'data-start="1"', 1), encoding="utf-8")
        shutil.copytree(DEMO / "fig", work / "fig")
        run("frontmatter.py", "--authors", HERE / "authors.json", "--book", HERE / "book.json", "--into", manuscript)
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
