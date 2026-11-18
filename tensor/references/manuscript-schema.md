# Tensor 원고 형식 (JSON) — build.py 입력

원고는 **JSON 한 파일**(`work/book.json`)에 글만 쓴다. 표지·목차·Preview·워밍업 문제·TOPIC 부품·적용문제·연습문제·실전 문제·Review·빠른 정답·해설의 HTML 과 CSS 는 `scripts/build.py` 가 고정 부품으로 조립한다. HTML 을 직접 쓰거나 `<style>`·`style=` 을 넣는 길은 없다. 그래서 누가 만들어도 같은 모양이 나온다.

```bash
python <skill>/scripts/build.py work/book.json            # → work/book.json 옆에 book.html (흑백, 인쇄용)
python <skill>/scripts/build.py work/book.json -o work/book_color.html --color   # 컬러판(화면용): theme-mono 제거, fig/ → figc/
python <skill>/scripts/build.py work/ch08.json work/ch09.json -o work/book.html  # 여러 장을 한 책으로 (장마다 JSON 하나)
python <skill>/scripts/lint.py  work/book.html --inventory work/INVENTORY.md
python <skill>/scripts/render.py work/book.html --strict --png work/preview/
```

build.py 는 필수 부품·순서·분량 규칙을 어기거나 **사용자 승인 기록(`approval`)이 없으면** 오류를 모두 출력하고 파일을 쓰지 않는다. 오류 메시지의 위치(`TOPIC 01 블록 7`)를 보고 JSON 을 고친다. `--lenient` 는 분량(개수·글자 수) 규칙만 경고로 낮추며, 사용자가 허락한 말이 `approval.lenient` 에 있어야 쓸 수 있다.

만든 `book.html` 에는 **도장**(`<meta name="tensor-build">`, 내용 해시)이 찍힌다. 한 글자라도 손으로 고치거나 HTML 을 직접 쓰면 도장이 맞지 않아 `render.py` 가 조판을 거부하고 `lint.py` 가 경고한다. `frontmatter.py` 는 도장이 맞는 원고에만 앞부분을 넣고 다시 도장을 찍는다.

완성 견본: `references/example-manuscript.json` (회로이론 14장 TOPIC 01 시안, 배포본에서도 같은 경로). 쓰기 전에 한 번 읽고, 쓴 뒤 나란히 비교한다.

---

## 1. 글 쓰는 규칙 (모든 문자열 공통)

- 문자열은 HTML 조각이다. 허용 태그는 **`<b> <i> <u> <sub> <sup> <span> <br> <small> <code>`** 뿐이다. `<div>`, `<p>`, `<table>`, `style=` 은 오류.
- 교재 용어 태그: `<span class="tg ws">원서 개념</span>`, `<span class="tg">시험 개념</span>`, `<span class="tg ind">원서 간접 개념</span>`, 각주 표시 `<sup class="pc">ⓐ</sup>`.
- 수식은 KaTeX `$…$`(인라인), `$$…$$`(별행). JSON 안이므로 백슬래시는 두 번 쓴다: `"$$v_o(t)=20-12.5e^{-0.25t}\\ \\text{V}$$"`, `"$\\tau=R_{\\mathrm{th}}C$"`. 수식 안의 `<`, `>` 는 그대로 써도 된다(빌더가 처리).
- 문체는 `writing-style.md` 를 따른다(평서문, 말풍선만 구어체, 대시 없음).

## 2. 최상위 구조

```json
{
  "scope": "chapter",                      // chapter = 장 전체(기본) / draft = TOPIC 시안
  "subject": "회로이론",
  "chapter": {"no": "14", "title": "라플라스 변환", "title_en": "The Laplace Transform"},
  "part": "Part2", "start_page": 16, "theme": "mono",          // theme: mono(기본) / color
  "per_page": 2,                           // 문제 쪽당 2(기본) 또는 4
  "sources": {                             // 출처 이름 선언 (필수). 출처 문자열은 이 이름 또는 "자체 제작"으로 시작한다
    "원서": {"title": "Dorf, Introduction to Electric Circuits 9e", "chapters": [14]},
    "보조": {"title": "Lafore, Data Structures & Algorithms in Java 2e", "chapters": [3, 14]},
    "강의": {"title": "강의록"}
  },
  "cover_note": "",                        // 선택. 장 표지 안내문 뒤에 작게 붙는 한 줄
  "plan": [{"no": "01", "title": "응답식에서 회로 읽기"}, …],   // 승인받은 TOPIC 구성안 전체 (시안이면 안 만든 TOPIC 도 적는다)
  "approval": { … },                        // 사용자 승인 기록 (필수, 아래)
  "preview": {"paragraphs": ["…", "…", "…"]},                 // 정확히 3문단 (writing-style §4-14)
  "warmup_note": "", "warmup": [ 문제 … ],                     // 워밍업 문제 W·01… (문제마다 pre = [준비] 칸)
  "topics": [ TOPIC … ],
  "apply_note": "", "apply": [ 문제 … ],                       // 적용문제 A·01…
  "exercises_note": "", "exercises": [ 문제 … ],               // 연습문제 B·01…
  "exam_note": "", "exam": [ 문제 … ],                         // 실전 문제 X·01… (장마다 5개, 1-B 의 시험 형식 그대로)
  "review": {"paragraphs": ["…", "…"]},                        // OVERVIEW 2문단. O/X 문항은 TOPIC 의 ox 에서 모은다
  "answers": [{"for": ["W·01", "01-EX01"], "text": "$C=2$ F"}, …]   // 모든 W·EX·A·B·X 의 답 (빠짐없이) → 빠른 정답·해설 장
}
```

### 승인 기록 `approval` (필수)

제작 전 확인(SKILL.md 1-B)과 TOPIC 구성안 승인(2단계)에서 **사용자가 한 말을 그대로** 옮긴다. 답을 받기 전에는 원고를 쓰지 않으므로, 이 칸을 채울 수 없으면 아직 원고를 쓸 때가 아니다. 지어 넣지 않는다.

```json
"approval": {
  "answers": {
    "materials": "강의록 L9~19 다 넣었고 해설집은 없어. 답은 시뮬레이션으로 검증해서 써.",   // 자료 점검·누락 자료 처리
    "scope": "12장 전체",                                                              // 범위 (장 전체 / TOPIC 시안)
    "exam": "서술형, 손추적이랑 손코딩 위주. 계산기 없음.",                             // 시험 형식
    "layout": "쪽당 2문제, 흑백이랑 컬러 둘 다",                                         // 문제 쪽 배치·출력
    "figures": "알아서 해 → 다시 그리기(기본)"                                           // 그림 방식. 맡긴 경우 그 말과 고른 기본값
  },
  "plan": ["01 반으로 나눈 뒤 어디서 정렬하는가", "02 두 앞머리로 합병하기", …],      // 승인한 구성안: "번호 제목" 목록
  "plan_ok": "이대로 진행해",                                                           // 구성안을 승인한 말
  "lenient": ""                                                                          // 선택. --lenient 를 허락한 말
}
```

- `answers` 의 다섯 칸과 `plan_ok` 는 비었거나 `{{…}}`·`TODO`·`미정` 같은 자리표시면 오류다.
- `approval.plan` 이 지금의 `plan`(`"번호 제목"`)과 한 글자라도 다르면 오류다. 구성안을 바꿨으면 바뀐 표를 다시 보여 주고 승인받아 두 칸을 갱신한다.

`sources.chapters` 를 적으면 출처 문자열의 장 번호(`14.7-1`, `R-8.3`, `Listing 5.3` 의 앞 수)가 선언된 장과 다를 때 오류가 난다. 보조 교재의 장 번호를 원서 장 번호와 섞는 실수를 막는다.

## 3. 문제 (warmup / apply / exercises / exam 의 원소)

```json
{"lv": 2, "src": "원서 P14.7-6 · 강의 p.12", "topic": "01",
 "pre": "정상상태에서 커패시터는 개방이다. 1차 응답의 시정수는 $\\tau=R_{th}C$ 이다.",   // warmup 만. 정의·규칙 한두 줄, 답은 쓰지 않는다
 "hint": "분자 6은 독립 정보인가?",
 "text": "그림의 회로에서 … 의 값을 구하시오.",
 "fig": {"src": "fig/a01.svg", "width": "62mm", "from": "원서 Fig P14.7-6 p.747"}}
```

- 번호(`W·01`, `A·01`, `B·01`, `X·01`)는 순서대로 자동. 다른 글자는 없다. `lv` 1~3, `topic` 은 관련 TOPIC 번호(쪽 번호 칸에 쓰인다), `hint` 는 한 줄.
- `fig` 는 객체 또는 객체 목록(`cap` 선택). 그림이 정말 필요 없는 문제만 `"nofig": "이유"` 를 쓴다. 둘 다 없으면 오류.
- **모든 그림 객체에 `from`(원본)이 필수다**(본문 블록·해법 단위 안의 그림 포함): `"원서 Fig 14.7-6 p.747"`, `"강의 p.12"`, `"보조 Fig 3.2"`, `"자체 제작"`. 출처 이름은 `sources` 에 선언한 것이어야 하고 장 번호도 검사한다. 원서·강의 그림을 **SVG 로 다시 그렸으면** 출력 폴더의 `compare/<그림 이름>.png`(`figtools.py compare 원본.png fig/a01.svg -o compare/a01.png`)가 있어야 하고 그림 파일보다 새것이어야 한다. 원본을 잘라 쓴 PNG 와 자체 제작 그림은 대조 시트가 필요 없다.
- 실전 문제(X)의 출처는 `실전 · 근거`(강의 랩 함정, 시험 복기 유형 등)로 쓴다. 시험 형식이 T/F·단답이면 지문 끝을 `(T/F)` 또는 질문으로 끝내도 된다.
- 문제 쪽 그림 폭 60~76mm. 파일은 `book.html` 이 놓일 폴더 기준 상대 경로이고, 없으면 오류.

## 4. TOPIC

```json
{"no": "01", "title": "응답식에서 회로 읽기",
 "ox": ["응답식 $A+Be^{-pt}$의 세 숫자가 각각 회로의 무엇인지 말할 수 있는가?", "…", "…"],   // Review O/X 3~5개
 "blocks": [ 블록 … ]}
```

`blocks` 는 쪽을 신경 쓰지 않고 순서대로 쓴다(쪽 나눔은 자동). 블록은 문자열 또는 `{"type": …}` 객체다.

| 블록 | 쓰는 법 | 비고 |
|---|---|---|
| 문단 | `"문장…"` 또는 `{"type":"p","text":"…","keep_next":true}` | `keep_next` 는 다음 부품과 같은 쪽에 둔다(연결 문단) |
| 소절 제목 | `"## 1. 응답식의 세 숫자"` | TOPIC당 2~3개. `"### "` 는 h4 |
| 흐름 칩 | `{"type":"flow","chips":["회로","KVL·KCL<br>미분방정식","…","응답식"],"rev":"시험은 이 순서를 거꾸로 묻는다"}` | 마지막 칩이 강조 |
| **EX** | `{"type":"ex","src":["원서 Example 14.7-1","강의 p.12"],"text":"…구하시오.","fig":{"src":"fig/ex01.svg","width":"60mm"}}` | 번호 자동(EX 01…). `fig` 또는 `nofig` 필수 |
| **원서적 해법** | `{"type":"sol","kind":"book","units":[ 단위 … ]}` | 첫 EX 바로 다음에 필수 |
| **시험적 해법** | `{"type":"sol","kind":"exam","cond":"적용 조건 한 줄","units":[ … ]}` | `cond` 필수 |
| **말풍선** | `{"type":"bubble","text":"응답식을 다 줬는데… 이걸 또 s영역으로 풀어야 해?"}` | 구어체 한 문장 |
| 논증 단계 | `{"type":"steps","units":["<b>최종값 정리</b> : …","…"]}` | 번호 대신 `·` (원서 개념으로 논증할 때) |
| 각주 | `{"type":"fn","key":"ⓐ","text":"…"}` | 참조한 블록 **바로 뒤**에 둔다 |
| **개념 박스** | `{"type":"concept","kind":"exam","title":"1차 응답식 해부","units":[ … ],"cond":"적용 조건"}` | `kind`: exam(시험 개념, 기본)/book(원서 개념)/ind(원서 간접 개념). 3탭은 자동. exam 은 `cond` 필수 |
| **CORE** | `{"type":"core","cond":"응답식이 주어진 역추적 문제","action":"상수 = 최종값 … 미지수와 맞춘다"}` | `[조건] ⟹ [행동]` 으로 조판 |
| 저자 TIP | `{"type":"tip","title":"끝까지 풀지 않는 용기","text":"…"}` | TOPIC당 1개 이하, 장 전체 2~3개 |
| **채점 포인트** | `{"type":"grade","intro":"이 유형이 어떻게 채점되는지 1~2문장","items":["…","…","…","…"]}` | 4~6줄 |
| **강의 VS 연습문제** | `{"type":"vs","rows":[["강의 Ex 14.7-1","1차 회로, 응답식이 식으로 주어짐"],…],"after":"표 뒤 마무리 1~2문장"}` | 4~6행 |
| 그림 | `{"type":"fig","src":"fig/x.svg","width":"62mm","cap":"설명"}` | 본문 그림 52~62mm |
| 코드 | `{"type":"code","text":"for (…) {…}","cap":"Listing 5.3"}` | 프로그래밍 과목. HTML 없이 그대로, 강조 줄은 `[[b]]…[[/b]]` |
| 배열 한 줄 | 문자열 안 매크로 `[[arr 5 2 _ 9 \| idx=0 \| hl=1 \| dark=3 \| dim=0-1 \| bar=2 \| mark=0:L,3:R \| lab=pass 1 \| cap=교환 1회]]` | 자료구조. `_` 빈칸, `~` 공백, hl 굵은 테두리, dark 강조 칸, dim 확정 영역, bar 칸막이 |
| 강의 랩 노트 | `{"type":"concept","kind":"ind","title":"강의 랩 노트 : …","units":["…","…"]}` | 랩·실습 자료가 있을 때 첫 CORE 뒤. 측정 수치, 흔한 구현 실수, 슬라이드 정정 |
| 표 | `{"type":"table","head":["…"],"rows":[["…","…"]]}` | |
| 강제 쪽 넘김 | `{"type":"pagebreak"}` | 꼭 필요할 때만 |

**단위(units)** — 해법·개념 박스 안에 들어가는 것. 문자열은 단계(①②③ 자동 번호)다.

```json
"units": [
  "<b>$t<0$</b> : 정상상태이므로 …",                               // 단계, 번호 자동
  {"n": "③", "step": "…"},                                        // 번호 지정
  {"p": "응답식의 세 숫자를 … $$…$$"},                              // 문단
  {"fig": {"src": "fig/ex01_dead.svg", "width": "78mm", "cap": "전원을 끈 회로"}},
  {"withfig": {"units": ["…", "…"], "fig": {"src": "fig/ex01_s.svg", "width": "62mm"}}},   // 글 왼쪽·그림 오른쪽
  {"table": {"head": ["숫자", "의미", "구하는 회로"], "rows": [["$A$", "최종값", "…"]]}},
  {"code": "…"}
]
```

### TOPIC 하나의 필수 순서 (빌더가 검사)

```
"## 1. …"  →  도입 문단(근거 번호)  →  EX 01  →  원서적 해법  →  관찰 문단  →  (연결 문단, keep_next)
→  말풍선  →  시험적 해법(cond)  →  원서 개념으로 논증(steps·fn)  →  개념 박스(exam, cond)  →  CORE
→  (TIP)  →  EX 02 …  →  채점 포인트  →  강의 VS 연습문제
```

- 빠지면 오류: EX, 원서적 해법, 말풍선, 시험적 해법, 시험 개념 박스, CORE, 채점 포인트, VS 표, 소절 제목, 도입 문단, 관찰 문단.
- 순서가 어긋나면 오류: 첫 EX 다음은 원서적 해법 / EX → 원서적 → 말풍선 → 시험적 → 개념 박스 → CORE / 채점 포인트·VS 표는 개념 박스 뒤.
- 분량(`--lenient` 로만 완화): **TOPIC 본문 한글 1,500자 이상**(수식·태그 제외, 견본 TOPIC 01 은 약 2,300자), 첫 EX 의 원서적 해법 3단계 이상, EX 2~3개, 소절 2~3개, 채점 4~6줄, VS 4~6행, ox 3~5개, Preview 3문단, Review 2문단, 장 전체 TOPIC 6~12개, 워밍업 2개 이상, 연습문제 4개 이상, 실전 문제 5개, TOPIC마다 적용문제 1개 이상.

본문 속 코드 조각은 `<code class="c">…</code>`, 트리·그래프 그림은 `scripts/dsfig.py` 로 SVG 를 만들어 `fig` 로 넣는다.

## 5. scope 와 시안

- `"scope": "draft"`: 한 TOPIC 시안. `plan` 에는 구성안 전체를 적고 `topics` 에는 만드는 TOPIC 만 넣는다. 목차에서 안 만든 TOPIC 은 `—` 로 표시된다. 연습문제(B)·실전 문제(X)는 생략 가능, 적용문제는 2개 이상.
- `"scope": "chapter"`: `plan` 의 모든 TOPIC 원고가 있어야 한다.

## 6. 빠른 정답·해설

`answers[].for` 에는 문제 번호를 쓴다: `W·01`, `A·02`, `B·03`, `X·01`, EX 는 `"{TOPIC}-EX{번호}"` (예: `"01-EX02"`). 같은 문제가 W 와 EX 에 중복되면 한 항목에 둘 다 적는다. `label` 을 생략하면 `W·01 / EX 01` 처럼 자동으로 만든다. `text` 는 답과 핵심 근거 한 줄, 코드 답은 `"code"` 에 따로 쓴다. 빌더가 워밍업 → 적용 → 연습 → 실전 순서의 **빠른 정답·해설** 장(Review 뒤, 자동 쪽 나눔)으로 만든다. 모든 번호에 답이 있어야 빌드된다. 답은 sympy·시뮬레이션 등으로 검증한 값만 쓰고, 원서 정답이 틀렸으면 "원서 정답 정정" 이라고 적는다.

## 7. 여러 장을 한 책으로

장마다 JSON 을 하나씩 쓰고(`work/ch08.json`, `work/ch09.json` …) 한 번에 빌드한다. 첫 장의 `start_page` 부터 쪽 번호가 이어지고, 목차·PAGE 칸·꼬리말은 장마다 따로 계산된다. 장마다 `plan`·`approval` 을 따로 둔다. 장별 HTML 을 이어 붙이지 않는다(도장이 맞지 않아 조판되지 않는다).

```bash
python <skill>/scripts/build.py work/ch08.json work/ch09.json work/ch10.json -o work/book.html
```

## 8. 결과 쪽 순서

장 표지 → 장 목차 → Preview → 워밍업 문제(W) → TOPIC … → 적용문제(A) → 연습문제(B) → 실전 문제(X) → Review: 개념진단(O/X, 넘치면 자동으로 다음 쪽) → 빠른 정답·해설. 책 전체의 앞부분(서문·전체 차례)은 `frontmatter.py` 가 `<!-- FRONTMATTER -->` 자리에 끼운다.
