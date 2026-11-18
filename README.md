# Tensor — 강의록 + 원서로 만드는 시험 특화 교재 스킬

**강의록 PDF + 원서 PDF, 딱 두 개만 넣으면** 수능 개념서처럼 짜인 대학 과목 시험 대비 교재를 **A4 인쇄용 PDF**로 만들어 주는 Claude 스킬입니다.

![데모 미리보기](docs/preview.png)

📄 **데모 PDF**: [`examples/demo/demo.pdf`](examples/demo/demo.pdf) (회로이론 14장 라플라스 변환, TOPIC 01 · 11쪽 · 문제는 전부 자체 제작)

---

## 무엇이 다른가

원서는 모든 내용을 같은 무게로, **개념 → 문제** 방향으로 씁니다. 시험장에서 필요한 건 반대 방향, **문제를 보는 순간 무엇을 의심할지**입니다. Tensor는 원서를 다시 쓰는 대신 **읽는 순서와 무게를 시험 기준으로** 바꿉니다.

| 장치 | 내용 |
|---|---|
| **개념 3분류** | 원서 개념 / 원서 간접 개념 / **시험 개념**(원서 본문엔 없지만 예제·연습문제에 반복되는 것) |
| **해법 두 층** | 같은 문제를 **원서적 해법**(정석)과 **시험적 해법**(지름길)으로 나란히. 지름길은 반드시 원서 개념으로 증명 |
| **강의 선정 문제** | 강의록 예제는 대부분 원서 문제입니다. 원서 번호로 대응시켜 장 첫머리에 모읍니다 — **족보 없이도** 됩니다 |
| **채점 포인트** | 대학 시험은 서술형 부분점수. 어떤 줄이 점수가 되는지 TOPIC마다 정리 |
| **검증** | 모든 답을 sympy로 계산 확인, 회로도는 다시 그려서 확인, 쪽 넘침 자동 검사 |

---

## 설치

### A. Claude Code (터미널) — 아래를 그대로 복사해서 붙여넣기

```bash
git clone https://github.com/legojmon/tensor-textbook-skill.git /tmp/tensor-textbook-skill
mkdir -p ~/.claude/skills
cp -r /tmp/tensor-textbook-skill/tensor ~/.claude/skills/tensor
bash ~/.claude/skills/tensor/scripts/setup.sh
```

### B. claude.ai / Claude 데스크톱 앱

1. **[tensor.zip 다운로드](https://github.com/legojmon/tensor-textbook-skill/raw/main/dist/tensor.zip)**
2. 설정 → **Capabilities** 에서 **코드 실행 및 파일 생성**을 켭니다.
3. **Customize → Skills → `+` → Create skill → Upload a skill** 에서 `tensor.zip` 업로드
4. 첫 사용 때 Claude가 `setup.sh`를 실행해 KaTeX·글꼴·회로도 라이브러리를 설치합니다.

> 메뉴 위치는 바뀔 수 있습니다. 공식 안내: [Using Skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude)

---

## 사용 — 프롬프트 복붙

**강의록 PDF와 원서 PDF를 첨부**하고 아래를 그대로 붙여넣으세요. 장 번호는 강의록에서 자동으로 찾습니다.

```text
Tensor 스킬로 첨부한 강의록이랑 원서로 교재 만들어줘.
```

범위나 옵션을 정하고 싶으면 한 줄씩 덧붙이면 됩니다.

```text
Tensor 스킬로 첨부한 강의록이랑 원서로 교재 만들어줘.
- 범위: TOPIC 01 시안만          (기본: 장 전체 — TOPIC 목록을 먼저 보여줌)
- 해설집도 첨부했어              (있으면 답 대조에 씀)
- 강의록 뒤에 채점 기준이 있어   (채점 포인트 박스의 근거로 씀)
- 포인트색은 #0E7C66
```

### 스킬이 하는 일

```
① extract.py   원서에서 해당 장 찾기 · 예제/연습/장끝문제 목록 · 강의 예제 ↔ 원서 번호 자동 대응 · 쪽 이미지
② TOPIC 설계   장 끝 문제에서 반복되는 '결정적 관찰'을 시험 개념으로 묶기
③ 그림         원서 그림을 보고 회로도를 다시 그림 (잘라 붙이지 않음)
④ 원고         TOPIC 본문은 블록만 순서대로 — paginate.js 가 A4 쪽 나눔 · 해법 박스 이어붙이기 · 쪽번호 · 탭 · 목차까지 자동
⑤ 검증         모든 답 sympy 계산 + 원서 답·해설집 대조
⑥ 렌더링       render.py → PDF + 쪽 넘침 검사 + 미리보기로 체크리스트 검수
```

> 강의록 예제는 대부분 원서 예제·연습문제를 그대로 옮긴 것이라, ①에서 원서 번호와 짝지어 `[원서 Example 14.7-1 · 강의 p.12]` 처럼 표기합니다. 족보가 없어도 됩니다.

결과로 **A4 PDF**(바로 제본 가능)와 원본 HTML이 나옵니다. 브라우저 엔진이 없는 환경이면 HTML을 Chrome에서 열어 **A4·여백 없음·배경 그래픽 켜기**로 PDF 저장하면 똑같이 나옵니다.

---

## 책 구성 (Part2 한 장)

```
Chapter 표지 → 목차 → Preview → 강의 선정 문제(L)
→ TOPIC 01 … TOPIC nn
     도입 → EX → 원서적 해법 → 생각 말풍선 → 시험적 해법
     → 원서 개념으로 증명 → 시험 개념 박스 → CORE → TIP
     → 답안·채점 포인트 → 강의 vs 연습문제 표
→ 적용문제(A) → 연습문제(B, 원서 장 끝 문제) → Review: 개념진단
```

- 과목 1개 = Part1 「원서 개념의 정리」 + Part2 「시험 개념의 완성」
- 공부법(Method) 페이지는 기본으로 넣지 않습니다. Part 가이드라인 1쪽 + TOPIC 속 TIP으로 충분합니다.

## 폴더 구조

```
tensor/                    ← 스킬 본체 (이 폴더만 설치하면 됨)
├── SKILL.md                     ← 파이프라인 + 품질 체크리스트
├── references/
│   ├── content-rules.md         ← 개념 분류·시험 개념 추출·문제 출처·문체·검증
│   ├── book-format.md           ← 페이지 순서·HTML 부품 카탈로그·자동 쪽 나눔 규칙
│   └── example-manuscript.html  ← 완성 원고 예시 (품질 기준)
├── assets/
│   ├── tensor.css               ← 디자인 (색은 :root 변수 4개만 바꾸면 끝)
│   ├── paginate.js              ← 자동 쪽 나눔·쪽번호·탭·꼬리말·목차 쪽번호
│   └── template.html            ← 빈 틀
└── scripts/
    ├── setup.sh                 ← KaTeX, Pretendard, schemdraw, playwright 설치
    ├── extract.py               ← 강의록·원서(·해설집) 분석 → work/INVENTORY.md
    ├── render.py                ← HTML → PDF + 쪽 넘침 검사 + 미리보기 PNG
    └── circuits.py              ← 회로도·응답 그래프 헬퍼
examples/demo/             ← 자체 제작 문제로 만든 데모 (demo.html, figs.py, demo.pdf)
dist/tensor.zip            ← claude.ai 업로드용
```

직접 렌더링해 보기:

```bash
bash tensor/scripts/setup.sh
python3 examples/demo/figs.py
python3 tensor/scripts/render.py examples/demo/demo.html --png preview/

# 내 자료로 분석만 먼저 해보기
python3 tensor/scripts/extract.py --lecture 강의록.pdf --textbook 원서.pdf --out work/
```

---

## 저작권 안내

- 이 레포에는 **원서·강의록 내용이 들어 있지 않습니다.** 데모의 문제와 그림은 전부 자체 제작입니다.
- 스킬로 만든 교재는 여러분이 넣은 원서·강의록을 바탕으로 하므로 **개인 학습용**으로만 쓰고, 공유·판매하지 마세요.
- 스킬은 원서 그림을 잘라 붙이지 않고 다시 그리며, 원서 문장을 길게 옮기지 않도록 설계되어 있습니다.

## License

MIT
