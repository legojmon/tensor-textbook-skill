# Tensor 책 형식 (스켈레톤 · 페이지 · 부품)

수능 개념서식 구성(교과서 개념 → 수능 개념 2단 구조, 기출 연결, 개념진단)을 대학 과목으로 옮긴 형식이다.
CSS는 `assets/tensor.css`, 빈 틀은 `assets/template.html` 에 있다. 아래 HTML 조각을 복사해서 쓴다.

---

## 1. 책 구조

과목 1개 = 상·하 2권.

| 권 | Part | 입력 | 내용 |
|---|---|---|---|
| 상 | Part1 「원서 개념의 정리」 | 원서 본문 + 강의록 | 원서 개념·원서 간접 개념, 원서적 해법만 |
| 하 | Part2 「시험 개념의 완성」 | 원서 예제·연습문제 + 강의록 예제 | 시험 개념, 원서적 → 시험적 해법 |

사용자가 한 장만 원하면 그 장의 Part2(또는 요청한 Part)만 만든다. 원서 1장 = Chapter 1개, 장 번호는 원서 번호를 그대로 쓴다.

---

## 2. 페이지 순서 (Part2 한 장 기준)

1. **Chapter 표지** `.page.cover` — 보라 배경, 회색 아치, CHAPTER + 장 번호, 장 제목, 하단 점선 안내문
2. **Chapter 목차** `.page.toc` — Preview / 워밍업 W·01 / TOPIC 목록 / A·01, B·01 / X·01 실전 문제 / Review / 정답
3. **Preview** (짝수쪽) — PRE-VIEW 박스: 인사 → 이 장에서 다룰 것 → 〈학습 방법〉 ①~⑤ → MEMO
4. **워밍업 문제 (W)** — 쪽당 2문제, `W·01…`. 강의에서 다룬 예제·원서 문제 중 각 TOPIC의 EX 01이 해부할 것. **문제마다 `준비` 칸**에 풀이에 필요한 정의·규칙을 한두 줄로 넣어 처음 보는 사람도 풀 수 있게 하고, `data-hint`로 첫 걸음을 준다
5. **TOPIC nn** × 6~12 — TOPIC당 보통 3~6쪽
6. **TOPIC 적용문제 (A)** — 쪽당 2문제
7. **연습문제 (B)** — 쪽당 2문제 (원서 장 끝 Problems 선별, 원서가 둘이면 둘 다에서)
8. **실전 문제 (X)** — 쪽당 2문제, `X·01…05`. 시험 형식 그대로: T/F·단답(이유 한 줄) → 손추적(중간 상태) → 손코딩(변형). 강의 랩·실습 자료의 함정과 시험 복기 유형을 넣는다
9. **Review: 개념진단** — OVER-VIEW 글 + TOPIC별 O/X 체크표
10. **빠른 정답·해설** — Review 뒤 두 번째 `<article class="manuscript">` 안 `section.topic data-no="해설"`. W → A → B → X 순서로 답과 핵심 근거 한 줄, 코드 답은 `pre.code`

워밍업을 앞에 두는 이유: 장을 시작할 때 "무엇을 풀 수 있어야 하는가"를 먼저 보여 주고, 본문 EX 01이 그 문제를 해부한다. 실전 문제를 뒤에 두는 이유: 본문과 연습문제를 마친 뒤 시험 시간처럼 풀어 보는 마무리이다.

쪽 번호: 짝수쪽은 왼쪽 아래(쪽번호 | 장 이름), 홀수쪽은 오른쪽 아래(TOPIC 이름 | 쪽번호).
홀수쪽 오른쪽 위에 `Part2` 탭과 `TOPIC nn` 탭.

---

## 3. 원고 구조와 자동 쪽 나눔 (paginate.js)

```html
<body data-chapter="14" data-chtitle="라플라스 변환" data-part="Part2" data-start="16">
  <section class="page cover">…</section>                       <!-- 고정 쪽 -->
  <section class="page toc">… <td class="pg" data-ref="topic-01"></td> …</section>
  <section class="page" data-id="preview">…</section>
  <section class="problems" data-id="warmup" data-title="워밍업 문제" data-per="2">…</section>
  <article class="manuscript">                                   <!-- 본문: 자동 쪽 나눔 -->
    <section class="topic" data-no="01" data-title="응답식에서 회로 읽기"> 블록… </section>
    <section class="topic" data-no="02" data-title="…"> 블록… </section>
  </article>
  <section class="page" data-id="a01" data-run="TOPIC 적용문제">…</section>
  <section class="problems" data-id="exam" data-title="실전 문제" data-per="2">…</section>
  <section class="page" data-id="review" data-run="Review: 개념진단">…</section>
  <article class="manuscript">                                   <!-- 빠른 정답·해설 -->
    <section class="topic" data-no="해설" data-title="빠른 정답·해설"> <h3>워밍업 문제</h3> <p><b>W·01</b> …</p> … </section>
  </article>
</body>
```

paginate.js 가 하는 일
- TOPIC마다 첫 쪽에 `topic-band` + `topic-title`, 이어지는 쪽에 `topline`.
- 블록이 넘치면 다음 쪽으로. **`.sol` 해법 박스는 단계 단위로 쪼개** 다음 쪽에 라벨 없이 이어 붙인다.
- `h3`, `h4`, `.keep-next` 는 다음 블록과 같은 쪽으로 따라간다(제목·연결 문단이 쪽 끝에 홀로 남지 않게).
- `.fn` 각주는 그 블록이 놓인 쪽 아래로 보내고 본문 높이를 줄인다. 참조(ⓐ)가 있는 블록 **바로 뒤에** 쓴다.
- `<div class="pagebreak"></div>` = 강제 쪽 넘김.
- 모든 쪽에 쪽 번호(`data-start` 부터), 짝/홀, 꼬리말, 홀수쪽 `Part2`·`TOPIC nn` 탭을 붙인다. 꼬리말 제목은 `data-run` > TOPIC 이름(홀수) > 장 이름(짝수).
- 목차의 `data-ref="topic-01" | "preview" | "a01" | …` 칸에 실제 쪽 번호를 채운다.
- 고정 쪽은 자동으로 넘기지 않는다 → 문제 쪽은 4문항, Preview·Review는 한 쪽 분량으로 쓴다. 넘치면 render.py 가 [넘침] 경고를 낸다.

## 4. 부품 카탈로그

### TOPIC 머리
```html
<div class="topic-band">14 &nbsp;라플라스 변환</div>
<div class="topic-title"><span class="no">TOPIC <i>0</i>1</span>응답식에서 회로 읽기</div>
<h3>1. 응답식의 세 숫자</h3>
```

### EX
```html
<div class="ex">
  <div><span class="badge">EX<span>01</span></span><div class="src">[원서 Example 14.7-1<br>강의 p.12]</div></div>
  <div class="withfig">
    <div class="txt q">문제 지문 … $$v_o(t)=16-12e^{-0.6t}\ \text{V}$$ …</div>
    <div class="fig"><img src="fig/ex01.svg" style="width:60mm"></div>
  </div>
</div>
```

### 해법 박스
```html
<div class="sol"><span class="lab"><span class="a">원서적</span><span class="b">해법</span></span>
  <div class="box">
    <div class="step"><span class="n">①</span><span>…</span></div>
  </div></div>

<div class="sol exam"><span class="lab"><span class="a">시험적</span><span class="b">해법</span></span>
  <div class="box"> … </div></div>
```
쪽을 넘어 이어지는 박스는 다음 쪽에서 `<div class="sol" style="margin-top:0"><div class="box" style="margin-top:0">` 로 라벨 없이 잇는다.

### 생각 말풍선
```html
<div class="bubble"><span class="dots">∘○</span><span class="b">응답식을 다 줬는데… 이걸 또 s영역으로 풀어야 해?</span></div>
```

### 개념 박스 (3탭 중 하나만 `.on`)
```html
<div class="concept">
  <div class="hd"><div class="ttl"><span class="ico">시험<br>개념</span>1차 응답식 해부</div>
    <div class="tabs"><span>원서 개념</span><span class="on">시험 개념</span><span>원서 간접 개념</span></div></div>
  <div class="body"> … (표 가능: <table><tr><th>…) </div>
</div>
```
아이콘 글자: 원서 개념 → `원서<br>개념`, 원서 간접 개념 → `간접<br>개념`.

### 본문 속 개념 태그
```html
<span class="tg ws">원서 개념</span>  <span class="tg">시험 개념</span>
<span class="tgk"><span class="tg">시험 개념</span><span class="tg">1차 응답식 해부</span></span>
```

### CORE (한 줄 요약)
```html
<div class="core"><span class="lab">CORE</span><div class="box">[조건] ⟹ [행동]</div></div>
```

### 저자 TIP
```html
<div class="tip"><div class="lab"><small>저자의 특강</small><b>TIP</b></div><div class="hd">제목</div>
  <div class="body"><p>…</p></div></div>
```

### 답안·채점 포인트 (대학 시험 특화)
```html
<div class="grade"><div class="hd"><span>✎ 답안 · 채점 포인트</span><small>대학 시험 특화</small></div>
  <div class="body"><p>…</p><ol><li>…</li></ol></div></div>
```

### 강의 vs 연습문제 표
```html
<div class="vs"><span class="lab">강의 <span class="v">VS</span> 연습문제</span>
  <table><tr><th>출처</th><th>출제 요소</th></tr><tr><td>…</td><td>…</td></tr></table></div>
```

### 각주 (본문에 없는 증명)
```html
<sup class="pc">ⓐ</sup>  …  <div class="fn"><span class="k">ⓐ</span> … 해설에 수록.</div>
```

### 흐름 칩
```html
<div class="flow"><span class="c">회로</span><span class="ar">→</span> … <span class="c end">응답식</span></div>
<div class="rev"><span class="line"></span><br>시험은 이 순서를 거꾸로 묻는다</div>
```

### 문제 페이지 (W / A / B / X) — 자동 배치
```html
<section class="problems" data-id="a01" data-title="TOPIC 적용문제"
         data-desc="TOPIC에서 만든 [시험 개념]을 바로 써 보는 문항이다.<br>원서 연습문제와 자체 제작 문항으로 구성한다." data-per="2">
  <div class="qitem" data-no="A·01" data-lv="1" data-src="원서 P14.7-6" data-topic="01">
    <div class="t">지문 … $$…$$ … 구하시오.</div>
    <div class="fig"><img src="fig/a01.svg" style="width:62mm"></div>
  </div>
  …
</section>
```
- `data-per="2"`(기본): 한 쪽에 **위·아래 2문제**, 지문 왼쪽·그림 오른쪽, 나머지는 풀이 공간. 대학 문제는 대부분 이것.
- `data-per="4"`: 짧은 계산 문제만 2×2.
- 문제 머리(번호·난이도 3칸·풀이 기록칸·출처·PAGE·TOPIC)는 data 속성으로 자동 생성. PAGE는 `data-topic` TOPIC의 첫 쪽.
- 첫 쪽에만 제목 박스(`qhead`)가 붙는다.
- 워밍업 문제의 `준비` 칸은 `.t` 맨 앞에 `<div class="pre"><b>준비</b>정의·규칙 한두 줄</div>` (CSS는 `scripts/prep.py`가 넣는다). 답을 알려 주지 말고, 정의·인덱스 규칙·연산 규칙만 쓴다.

### 빠른 정답·해설 장
Review 뒤에 두 번째 `<article class="manuscript">`를 열고 `<section class="topic" data-no="해설" data-title="빠른 정답·해설">`에 `h3`(워밍업 문제 / TOPIC 적용문제 / 연습문제 / 실전 문제)와 `<p><b>A·01</b> 답 …</p>`을 쓴다. 숫자가 아닌 TOPIC 번호에서는 "TOPIC" 글자와 탭이 필요 없으므로 원고 끝에 아래 스크립트를 넣는다(전체 차례에는 제목만 나온다).
```html
<script>
new MutationObserver(()=>{ if(document.body.dataset.ready!=="1") return;
  document.querySelectorAll('.page[data-topic="해설"]').forEach(p=>{
    const t=p.querySelector('.topic-title .no'); if(t) t.remove();
    const tb=p.querySelector('.tab-topic'); if(tb) tb.remove();
    const f=p.querySelector('.foot .ttl'); if(f) f.innerHTML='<span class="t">'+p.dataset.chapter+'</span>&nbsp; 빠른 정답·해설';
  });
}).observe(document.body,{attributes:true,attributeFilter:['data-ready']});
</script>
```
문체 검사(`lint.py`)는 이 장과 코드 블록을 건너뛴다.

### 강의 랩 노트 (실습·랩 자료가 있을 때)
관련 TOPIC의 첫 CORE 뒤에 원서 간접 개념 박스로 넣는다: `<div class="concept ind">` 제목 "강의 랩 노트 : …", 본문은 `.step` 2~3줄. 랩에서 측정한 수치(비교 횟수, 높이), 흔한 구현 실수, 슬라이드 정정 사항을 쓴다.

### Preview
`template.html` 의 Preview 쪽을 그대로 쓰고 문단만 바꾼다. 〈학습 방법〉 항목: ① 워밍업(준비 칸을 읽고 먼저 풀기) ② 본문(TOPIC) ③ 적용문제 ④ 연습문제 ⑤ 실전 문제(시간을 재고).

---

## 5. 그림
- 회로 과목: `scripts/circuits.py` (schemdraw). 자주 쓰는 토폴로지 builder가 있다. 새 토폴로지는 `drawing()`, `out_terms()`, `save()` 로 직접.
- 그 외 과목: matplotlib(그래프·좌표·블록도) 또는 직접 쓴 SVG. 선 굵기 1.1pt, 글꼴 Noto Sans CJK KR 12pt, 강조는 `#6B3FD4` 하나.
- 그래프: `plot_response()`.
- 자료구조·알고리즘 과목: `scripts/dsfig.py` — `tree()`(이진 `(키, L, R)` / 일반 `(키, [자식])`, 강조 노드·간선·주석·유령 노드), `graph()`(정점 좌표, 가중 간선, 방향, 강조), `row()`. 같은 키가 둘이면 `'5@a'`처럼 구분한다. 배열 한 줄은 그림 대신 `[[arr …]]` 매크로(`scripts/prep.py`)로 쓴다.
- 본문 그림 폭 52~62mm, 문제 페이지 그림 60~76mm. 시험적 해법용 "전원을 끈 회로"는 ACCENT 색으로 강조.

## 6. 흑백 인쇄 (기본)
- `template.html` 은 `tensor.css` 다음에 `theme-mono.css` 를 불러온다. 색 대신 **모양**으로 구분한다: 시험 개념 태그 = 검정 반전, 원서 개념 = 실선, 원서 간접 개념 = 점선(`.tg.ind`) / 개념 박스 = 이중선·실선·점선(`.concept`, `.concept.book`, `.concept.ind`) / 시험적 해법 = 굵은 왼쪽 막대, 원서적 해법 = 옅은 회색.
- 장·Part 표지의 보라색 면은 흑백에서 옅은 회색 바탕과 짙은 회색 표식으로 옮긴다. 장 번호·CHAPTER·Part 표기는 짙은 면에 흰 글씨, 제목·작은 안내문은 밝은 면에 짙은 글씨로 둔다. 본문 띠와 탭은 선으로 구분한다. 컬러로 뽑을 때만 `theme-mono.css` 링크를 지우고 `TENSOR_THEME=color`로 그림을 다시 만든다.

### 흑백·컬러 두 벌 한 번에
`python3 scripts/prep.py src.html book.html` (흑백) 과 `python3 scripts/prep.py src.html book_color.html --color` (컬러: theme-mono 링크 제거, `fig/` → 강조색 `figc/`)를 같은 원고로 돌리고 둘 다 렌더링한다. 인쇄는 흑백, 화면 학습은 컬러를 쓴다.

## 7. 색 바꾸기 (컬러 인쇄일 때)
`tensor.css` 맨 위 `:root` 의 `--p`(포인트), `--pl`(옅은 배경), `--pm`(중간), `--pd`(진한) 4개만 바꾸고, `circuits.py` 의 `ACCENT` 를 같은 값으로 바꾼다.
