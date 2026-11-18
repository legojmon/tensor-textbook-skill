"""Install the shared TENSOR rendering environment for the active Python interpreter."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

from render import BUILD

PACKAGES = ("playwright-core@1.65.0", "katex@0.16.22", "pretendard@1.3.9", "@fontsource/noto-serif-kr@5.3.1",
            "@fontsource/montserrat@5.3.0", "@fontsource/cormorant-garamond@5.3.0")


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
    from render import find_chrome
    got = subprocess.run(["node", str(BUILD / "node_modules/playwright-core/cli.js"), "install", "chromium"])
    if got.returncode != 0:
        if not find_chrome():
            raise SystemExit("Chromium 내려받기에 실패했고 설치된 Chrome도 찾지 못했습니다. Chrome을 설치하거나 TENSOR_CHROME 에 경로를 지정하세요.")
        print("Chromium 내려받기에 실패해 설치된 Chrome을 씁니다:", find_chrome())
    print(f"TENSOR 실행 환경 준비 완료 · {BUILD}")


if __name__ == "__main__":
    main()
