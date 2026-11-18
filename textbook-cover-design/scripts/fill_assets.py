#!/usr/bin/env python3
"""예시 표지(.dc.html)의 assets/ 경로를 캔버스에 업로드한 URL로 바꿔 새 폴더에 쓴다.

사용법:
    python3 scripts/fill_assets.py mapping.json out_dir [html ...]

mapping.json 예시 (upload_asset 결과의 url을 그대로 넣는다):
    {
      "assets/fonts/Pretendard-Light.woff2":   "/_blob/....",
      "assets/fonts/Pretendard-Regular.woff2": "/_blob/....",
      "assets/fonts/Pretendard-Medium.woff2":  "/_blob/....",
      "assets/fonts/Pretendard-Bold.woff2":    "/_blob/....",
      "assets/fonts/Pretendard-Black.woff2":   "/_blob/....",
      "assets/logo/snu-logo.png":              "/_blob/...."
    }

html을 생략하면 examples/tensor-circuit/ 의 front·back·spine을 처리하고,
캔버스 파일 이름(Main/Back/Spine.dc.html)으로 저장한다.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
DEFAULT = {
    "front.dc.html": "Main.dc.html",
    "back.dc.html": "Back.dc.html",
    "spine.dc.html": "Spine.dc.html",
}


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    mapping = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = pathlib.Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)

    if len(sys.argv) > 3:
        jobs = [(pathlib.Path(p), pathlib.Path(p).name) for p in sys.argv[3:]]
    else:
        ex = HERE / "examples" / "tensor-circuit"
        jobs = [(ex / src, dst) for src, dst in DEFAULT.items()]

    for src, dst in jobs:
        text = src.read_text(encoding="utf-8")
        for path, url in mapping.items():
            text = text.replace(path, url)
        if "assets/" in text:
            print(f"경고: {src.name}에 바뀌지 않은 assets/ 경로가 남아 있음", file=sys.stderr)
        (out / dst).write_text(text, encoding="utf-8")
        print(f"{src.name} -> {out / dst}")


if __name__ == "__main__":
    main()
