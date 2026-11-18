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

이 파일들은 Claude Design 캔버스 형식(`.dc.html`)입니다. 글꼴(Pretendard)과 서울대학교 로고는 캔버스에 올린 파일(`/_blob/...`)을 가리키므로, 캔버스 밖에서 열면 표시되지 않습니다. 다른 곳에서 쓰려면 해당 경로를 직접 가진 글꼴·로고 파일로 바꿔 주세요.

저자: 김준형 · 최재원
