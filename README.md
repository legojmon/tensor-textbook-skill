# TENSOR 교재 제작

강의록과 원서 PDF를 첨부하고 사용하는 도구에 맞는 프롬프트를 복사하세요.

**Claude**

```text
https://github.com/legojmon/tensor-textbook-skill 저장소의 tensor/SKILL.md를 읽고 첨부한 강의록과 원서로 TENSOR 교재를 만들어줘. 저장소를 열 수 없으면 dist/tensor.zip을 요청해. 같은 스킬의 setup.py와 selfcheck.py로 조판을 확인하고, 자료 누락과 시험 범위를 짚고 TOPIC 구성안을 보여줘. 내가 확인하면 내지와 앞·뒤표지, 책등, 펼침면 PDF를 만들어줘. 책 전체를 만들 때는 저자 원고와 사진을 받아 서문과 전체 차례도 넣어줘.
```

**Codex** · 이 저장소를 프로젝트로 연 뒤 사용하세요.

```text
$tensor 첨부한 강의록과 원서로 TENSOR 교재를 만들어줘. 견본 조판을 확인하고 TOPIC 구성표를 이 대화에 보여줘. 범위나 구성에서 내가 선택할 부분은 Codex 질문 카드로 물어봐. 한 TOPIC 시안을 선택하면 시안 PDF를 여기서 열어볼 수 있게 줘. 전체 제작을 진행하면 내지와 앞·뒤표지, 책등, 펼침면 PDF도 여기에 줘. 책 전체를 만들 때는 저자 원고와 사진을 받아 서문과 전체 차례도 넣어줘.
```

## 데모

[회로이론 14장 내지 PDF](examples/demo/demo.pdf) · 라플라스 변환, 자체 제작 예제와 연습문제

![회로이론 내지](docs/preview.png)

[표지와 책등 펼침면 PDF](examples/demo/cover/spread.pdf)

![표지와 책등](docs/cover.png)

[앞부분(커리큘럼·로드맵·소개·서문·저자 소개·Part 차례·가이드라인·Method I)이 있는 회로이론 견본](examples/opening/book.pdf) · [뒷표지 소개 글](examples/opening/back.pdf) · [저자 정보와 채울 항목](author/)

![앞부분 견본](docs/opening.png)

<details>
<summary>처음 설치하거나 같은 원고의 조판 결과를 확인할 때</summary>

Python 3.12와 Node.js/npm을 준비한 뒤 저장소 루트에서 실행하세요. Windows·macOS·Linux에서 같은 Python 진입점을 사용합니다. macOS·Linux에서 Python 실행 파일이 `python3`이면 아래 명령의 `python`을 바꾸세요.

```sh
python tensor/scripts/setup.py
python tensor/scripts/selfcheck.py
```

`selfcheck.py`는 공통 렌더러로 회로이론 견본을 PDF로 만든 뒤 기준 이미지와 쪽별로 비교합니다. 용지 크기와 쪽수가 같고, 각 쪽에서 명암 차이가 16/255를 넘는 픽셀이 2% 이하여야 통과합니다. 같은 원고·그림·글꼴을 사용한 결과를 비교합니다. 새로 집필한 문장은 모델에 따라 달라질 수 있습니다.

저자와 과목 입력 양식은 [앞부분 작성 지침](tensor/references/frontmatter.md)에 있습니다. Claude에 직접 가져오려면 [배포용 스킬](dist/tensor.zip)을 사용하세요.

</details>

원서와 강의 자료로 만든 교재는 개인 학습용으로 사용하세요. 서울대학교 로고는 학교 규정에 따라 사용하세요. 표지 설계 김준형 · 최재원. 코드 MIT License.
