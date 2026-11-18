---
name: textbook-cover-design
description: 교재 내지 PDF와 레퍼런스 표지 이미지를 바탕으로 A4 앞표지·뒷표지·책등을 Design 캔버스로 만들 때 사용. 과목명, 교재명, 저자, 학교 로고가 들어가는 인쇄용 교재 표지 제작.
---

# 교재 표지 제작 (앞표지 · 뒷표지 · 책등)

내지 PDF의 색·글꼴을 그대로 가져오고, 레퍼런스 표지의 **구성**(거대한 기하 도형 + 세로 대형 타이틀 + 모서리의 작은 자간 넓은 문구)을 빌려 오되, 도형은 **과목을 상징하는 기호**로 바꾼다.

## 이 폴더에 들어 있는 것 (따로 구할 필요 없음)
```
textbook-cover-design/
├── SKILL.md
├── assets/
│   ├── fonts/Pretendard-{Light,Regular,Medium,Bold,Black}.woff2   # 300/400/500/700/900, OFL-1.1
│   ├── fonts/OFL-LICENSE.txt
│   └── logo/snu-logo.png                                          # 서울대학교 로고 (컬러, 투명 배경)
├── examples/tensor-circuit/{front,back,spine}.dc.html             # 완성본 (assets/ 경로 사용)
└── scripts/fill_assets.py                                         # assets/ 경로 → 업로드 URL 치환
```

## 빠른 시작 (TENSOR 회로이론 표지를 그대로 다시 만들 때)
1. `list_types` → Design 타입으로 `create_from_type`.
2. `upload_asset`으로 `assets/fonts/` 5개 + `assets/logo/snu-logo.png`를 한 번에 올린다.
3. 결과의 url로 `mapping.json`(키 = `assets/...` 상대경로, 값 = `/_blob/...`)을 만들고
   `python3 scripts/fill_assets.py mapping.json <root>/project` 실행 → `Main/Back/Spine.dc.html` 생성.
4. `canvas.json`의 boards에 Main(0,0,794×1123,a4), Back(874,0,794×1123,a4), Spine(1748,0,57×1123)을 등록하고 `publish_files`(mode patch)로 올린다.
다른 과목·교재라면 아래 절차대로 고치되, 글꼴·로고는 2–3번을 그대로 쓴다.

## 0. 입력 확인
필요한 것: 내지 PDF, 레퍼런스 표지 이미지, **교재명(브랜드)**, **과목명**, 저자. (서울대 로고·Pretendard는 `assets/`에 있음)
- 교재명과 과목명을 혼동하지 말 것. 교재명(예: TENSOR)이 표지의 주인공(세로 대형 타이틀)이고, 과목명(예: 회로이론)은 우상단 보조 타이틀이다.
- 다른 학교 로고가 필요하면 학교 사이트에서 받을 수 없으므로(네트워크 차단) 사용자에게 PNG/SVG(투명 배경) 첨부를 요청하고 `assets/logo/`에 추가한다.

## 1. 내지 분석
```bash
pdfinfo 내지.pdf            # 판형 (A4 = 794×1123 px)
pdffonts -l 2 내지.pdf      # 글꼴 (예: Pretendard)
pdftoppm -r 50 -png -f 1 -l 3 내지.pdf p   # 미리보기 후 Read로 확인
```
PIL로 배경·포인트 픽셀을 찍어 hex를 얻는다 (예: 보라 #6B3FD4, 진회색 #4A4A52). 내지 문구(단계 설명, 헤더 문구)는 표지 카피 소재로 메모한다 — 표지 문구는 지어내지 말고 내지 문장을 다듬어 쓴다.

## 2. 캔버스 생성
- `list_types` → **Design** 타입으로 `create_from_type` (제목: "<교재명> <과목> 표지").
- 아트보드: `Main.dc.html`(앞표지), `Back.dc.html`(뒷표지), `Spine.dc.html`(책등). A4 고정 794×1123, `paper: "a4"`. 80px 간격으로 가로 배치.
- 사용자가 캔버스에서 직접 수정하므로, 수정 전에는 **항상 최신 파일을 read_file** 하고, 작은 변경은 `edit_version`(path 지정)으로 한다. 로컬 사본으로 통째로 덮어쓰지 말 것.

## 3. 글꼴: 내지와 같은 글꼴을 직접 올린다
Google Fonts의 Noto Sans KR은 영문이 어색해 보인다는 피드백이 있었다. Pretendard는 `assets/fonts/`에 이미 있다(다른 글꼴이 필요할 때만 `npm pack <패키지>`로 받는다).
`upload_asset`으로 5개 굵기를 올리고 `<helmet><style>`에 `@font-face`(300/400/500/700/900, `font-display:block`, `src:url(/_blob/...)`)로 등록. 모든 아트보드에서 같은 blob URL을 재사용.

## 4. 앞표지 구성 (794×1123)
- **도형(SVG, 절대배치)**: 과목 기호를 거대하게. 회로이론 예시 — 왼쪽 Ω(원 + 흰 구멍 + 아래 틈 + 양쪽 발), 오른쪽 커패시터(─┤├─: 위아래 리드선 직사각형 + 두 극판, 페이지 밖으로 블리드).
  - 곡선이 많은 기호(사인파 링 등)는 "밤티"라는 반응을 받았다. **굵은 직사각형·원 위주의 단순한 블록 형태**가 레퍼런스 느낌에 맞는다.
  - 그라데이션은 `gradientUnits="userSpaceOnUse"`로 도형들이 하나의 색 필드를 공유하게. 내지 포인트색 계열로 연한색→포인트색→인접 색상(예: #ECE6FE → #A88EF2 → #7A55DE → #5A6BDD).
  - 구멍·틈은 흰색 도형을 위에 덮어서 만든다.
- **세로 대형 타이틀**: 교재명 글자를 한 줄에 하나씩, 104–108px, weight 900, 진회색, `margin-left`를 번갈아 줘서 엇갈리게.
- **좌상단**: 자간 넓은(0.4em) 15px 3줄 태그라인 (예: 기본부터 / 심화까지 / 완성하는).
- **우상단**: 과목명 30px 900 + 아래 13px 보조 문구.
- **하단 좌**: 학교 로고(높이 52px, 비율 유지) + 영문 학교명 두 줄("Seoul National / University").
- **하단 우**: "저자1 · 저자2" 13px + "지음".
- 가장자리 여백 ≥48px, 색은 `data-props`로 `accent`/`ink` 노출.

## 5. 뒷표지
- 앞표지에서 왼쪽 밖으로 잘린 도형을 뒷표지 오른쪽 가장자리에 **같은 좌표 + 794px**로 그려, 펼쳤을 때 책등을 건너 이어지게 한다(그라데이션 좌표도 +794).
- 좌상단 교재명(포인트색) + 과목명, 중앙에 36px 제목 + 짧은 포인트색 바 + 내지 문장 기반 소개 2문단(15px, line-height 1.8, 폭 ~540px), 하단 점선 구분선 아래에 로고·학교명·저자.

## 6. 책등
- 폭 = 책 두께(모르면 15mm = 57px로 두고 알려 달라고 한다), 높이 1123.
- 배경: 포인트색 세로 그라데이션. 글자는 흰색, `writing-mode: vertical-rl`(한글은 서고 영문은 눕는 한국식 책등).
- 위: 교재명 → 짧은 구분선 → 과목명 → 보조 문구. 아래: 저자(세로) → 로고.
- 로고는 흰 배경 박스 없이 `filter: brightness(0) invert(1)`로 **로고 자체를 흰색** 처리(세부 문양이 뭉개지면 공식 반전 로고 파일을 요청).

## 7. 마무리
- 결과를 확인하려고 다시 읽거나 렌더링하지 말고, 바뀐 점과 가정(책등 두께, 지어낸 문구 여부)을 짧게 알린다.
- 다음 단계 제안: 실제 책등 두께 반영, 바코드/ISBN 자리, 앞·책등·뒤를 한 장으로 합친 인쇄용 펼침면.
