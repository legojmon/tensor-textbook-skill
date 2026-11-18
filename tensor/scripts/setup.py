"""Install the shared TENSOR rendering environment for the active Python interpreter."""
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import os
from pathlib import Path
import shutil
import subprocess
import sys

from render import BUILD

PACKAGES = ("playwright-core@1.65.0", "katex@0.16.22", "pretendard@1.3.9", "@fontsource/noto-serif-kr@5.3.1")


def main():
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not npm:
        raise SystemExit("Node.js와 npm을 설치하고 다시 실행하세요.")
    BUILD.mkdir(parents=True, exist_ok=True)
    manifest = BUILD / "package.json"
    if not manifest.exists():
        manifest.write_text('{"name":"tensor-render","private":true}\n', encoding="utf-8")
    subprocess.run([npm, "install", "--ignore-scripts", "--no-audit", "--no-fund",
                    "--save-exact", *PACKAGES], cwd=BUILD, check=True)
    requirements = Path(__file__).with_name("requirements.txt")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements)], check=True)
    subprocess.run(["node", str(BUILD / "node_modules/playwright-core/cli.js"), "install", "chromium"], check=True)
    print(f"TENSOR 실행 환경 준비 완료 · {BUILD}")


if __name__ == "__main__":
    main()
