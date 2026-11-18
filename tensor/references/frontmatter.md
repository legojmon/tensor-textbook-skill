# 책의 앞부분과 저자 원고

같은 저자 정보를 여러 과목에서 재사용한다. `assets/authors/authors.example.json`을 개인 작업 폴더에 복사한다. 책별 원고는 `book.example.json`을 복사해 채운다. 사진·서명 경로는 저자 JSON을 기준으로 지정한다.

저자에게는 [두 저자 작성지](../assets/authors/author-workbook.md)를 먼저 건넨다. 서문 초안은 책의 실제 예제를 바탕으로 제안하고, 두 저자가 직접 보내 준 장면과 한마디를 받아 다듬는다. 독자 수기, 학력, 성과, 연락처는 예시를 채우기 위해 만들지 않는다. 책 전체를 첫 쪽부터 조판할 때는 원고 JSON 의 `"start_page": 1`을 확인한다. 장만 발췌한 견본은 원래 시작 번호를 유지할 수 있다.

| 한 번 받을 자료 | 형식과 쓰임 |
| --- | --- |
| 저자명과 순서 | 표지·책등·저자 소개에 쓸 이름. 영문명은 저자가 준 표기 사용 |
| 사진과 약력 | 밝은 단색 배경, 명암이 뚜렷한 상반신 사진 권장. 저자별 약력 3~5줄과 독자에게 전할 한두 문장 |
| 선택 자료 | 서명 이미지, 정오·질문 창구, 시리즈 과목과 구성 |
| 책마다 받을 자료 | 과목, 일정, 서문 또는 키워드, 독자에게 전할 내용 3~5개, 선택적으로 게재 동의를 받은 실제 후기와 판권 정보 |

서문은 저자의 목소리로 다듬고, 약력·성과·일화는 받은 내용만 사용한다. 수기는 동의를 확인한 뒤 맞춤법만 고친다. 개인 자료는 저장소 밖이나 무시되는 `authors/` 및 `work/`에 둔다.

## 입력과 쪽 순서

1. `series`는 `{"subject":"회로이론","parts":["Part2"],"status":"예정"}` 형식의 배열이다. 과목별 자료가 있을 때만 커리큘럼 쪽을 싣는다.
2. `semester`는 `{"label":"중간시험","date":"실제 날짜"}`, `roadmap_steps`는 `{"when":"시험 전","what":"다시 볼 TOPIC"}` 형식이다.
3. `about`은 `{"title":"제목","text":"설명"}` 배열이다. `preface`는 문단 배열, `thanks`는 감사 문구다. 서문 뒤에는 제공된 서명만 넣는다.
4. 저자 소개에는 제공한 사진·약력·한마디를 넣는다. 책의 구성에는 흑백 범례와 문제·해법의 읽는 순서를 표시한다.
5. `testimonials`의 각 항목에는 `text`, `name`, `consent: true`가 필요하다. `contact`와 `colophon`은 표시 이름과 값의 쌍이다.
6. 전체 차례는 조판한 원고에서 장·TOPIC·문제·Review의 시작 쪽을 계산한다. 각 장 첫 표지의 `data-chapter`, `data-chtitle`을 지정한다. 단일 장은 body 값을 쓸 수 있다.
7. Part 표지와 가이드에는 `part.name`, `part.title`, `part.goals`, `part.checklist`를 사용한다. 빈 선택 항목은 생략한다.

`python tensor/scripts/frontmatter.py --authors authors/authors.json --book work/book.json --into work/book.html`을 실행한 뒤 평소와 같이 렌더링한다. 같은 명령을 다시 실행하면 기존 앞부분이 갱신된다. 최종 뒷표지의 `back_paras`에는 실제 Preview 또는 저자가 제공한 소개 원고에서 고른 문단을 넣는다.
