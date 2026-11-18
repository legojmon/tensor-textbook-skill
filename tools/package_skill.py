"""Create dist/tensor.zip from the same engine used by both repository entry points."""
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
import os
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "tensor"
DEMO = ROOT / "examples/demo"


def main():
    files = {Path("tensor/SKILL.md"): SKILL / "SKILL.md"}
    for folder in ("assets", "references", "scripts", "selfcheck/ref"):
        for path in (SKILL / folder).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and not path.name.startswith("."):
                files[path.relative_to(ROOT)] = path
    for path in [DEMO / "demo.html", *sorted((DEMO / "fig").glob("*.svg"))]:
        files[Path("tensor/selfcheck/demo") / path.relative_to(DEMO)] = path
    target = ROOT / "dist/tensor.zip"
    target.parent.mkdir(exist_ok=True)
    with NamedTemporaryFile(dir=target.parent, suffix=".zip", delete=False) as fh:
        temp = Path(fh.name)
    try:
        with ZipFile(temp, "w") as archive:
            for name, path in sorted(files.items()):
                member = ZipInfo(name.as_posix(), (2020, 1, 1, 0, 0, 0))
                member.external_attr = (0o100755 if path.suffix == ".sh" else 0o100644) << 16
                archive.writestr(member, path.read_bytes(), compress_type=ZIP_DEFLATED)
        os.replace(temp, target)
    finally:
        temp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
