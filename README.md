# tensor-textbook-skill

TENSOR 교재 제작에 쓰는 Claude 스킬 모음입니다.

## 스킬

| 폴더 | 설명 |
|---|---|
| [`textbook-cover-design/`](textbook-cover-design/SKILL.md) | 내지 PDF와 레퍼런스 표지를 바탕으로 A4 앞표지·뒷표지·책등을 디자인하는 방법 |

## 예시: TENSOR 회로이론 표지

`textbook-cover-design/examples/tensor-circuit/`에 실제로 만든 표지의 소스가 있습니다.

- `front.dc.html` — 앞표지 (A4, 794×1123)
- `back.dc.html` — 뒷표지 (A4, 794×1123)
- `spine.dc.html` — 책등 (15mm, 57×1123)

이 파일들은 Claude Design 캔버스 형식(`.dc.html`)입니다. 글꼴과 로고는 `textbook-cover-design/assets/`를 가리키며, 캔버스에 올릴 때 `scripts/fill_assets.py`로 업로드 URL로 바꿉니다. 자세한 절차는 SKILL.md의 "빠른 시작"을 보세요.

- 글꼴: Pretendard (SIL Open Font License 1.1, `assets/fonts/OFL-LICENSE.txt`)
- 로고: 서울대학교 로고 (`assets/logo/snu-logo.png`)

저자: 김준형 · 최재원
