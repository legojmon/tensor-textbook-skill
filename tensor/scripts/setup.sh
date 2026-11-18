#!/usr/bin/env bash
# Tensor 렌더링 환경 설치 (한 번만 실행)
#   - KaTeX(수식), Pretendard(제목 글꼴)  -> <skill>/.build/node_modules
#   - schemdraw(회로도), matplotlib(그래프), sympy(답 검증), playwright(PDF), pymupdf(미리보기)
set -e
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="${TENSOR_BUILD:-$SKILL_DIR/.build}"
mkdir -p "$BUILD"
cd "$BUILD"
[ -f package.json ] || echo '{"name":"tensor-build","private":true}' > package.json
npm install --silent katex pretendard

PIP="pip install -q"
python3 -m pip --version >/dev/null 2>&1 && PIP="python3 -m pip install -q"
$PIP schemdraw matplotlib sympy playwright pymupdf 2>/dev/null || \
  $PIP --break-system-packages schemdraw matplotlib sympy playwright pymupdf

# 시스템 Chrome/Chromium 이 없으면 playwright 내장 chromium 설치
if ! command -v google-chrome >/dev/null && ! command -v chromium >/dev/null && \
   ! command -v chromium-browser >/dev/null && \
   [ ! -d "/Applications/Google Chrome.app" ]; then
  python3 -m playwright install chromium || echo "[안내] chromium 설치 실패 — HTML을 브라우저에서 열어 A4로 인쇄(PDF 저장)해도 됩니다."
fi

# 본문 명조 글꼴 (Noto Serif CJK KR) 안내
if command -v fc-list >/dev/null && ! fc-list | grep -qi "Serif CJK KR"; then
  echo "[안내] 본문 글꼴 Noto Serif CJK KR 이 없습니다. (Ubuntu: sudo apt install fonts-noto-cjk)"
fi
echo "Tensor setup 완료: $BUILD"
