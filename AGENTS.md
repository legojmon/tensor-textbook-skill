# TENSOR 교재 저장소

Codex에서 교재를 제작하거나 TOPIC을 검토할 때는 `.agents/skills/tensor/SKILL.md`에서 시작한다. 이 진입점은 질문·전달 절차를 정하고 공통 제작 지침인 `tensor/SKILL.md`로 연결한다. Claude와 Codex는 `tensor/assets/`, `tensor/references/`, `tensor/scripts/`를 공유한다.

원고는 JSON(`tensor/references/manuscript-schema.md`)으로만 쓰고 `tensor/scripts/build.py`가 HTML을 조립한다. HTML·CSS를 손으로 쓰지 않는다. 제작 전 답과 TOPIC 구성안 승인을 사용자의 말 그대로 원고의 `approval`에 옮겨야 빌드되고, `build.py` 도장이 맞지 않는 HTML은 `render.py`가 조판하지 않는다. 조판 규칙(`tensor/assets/*.css`, `paginate.js`, `build.py`)을 수정한 뒤에는 `python tools/refresh_demo.py`로 데모와 기준 그림을 다시 만들고 `python tensor/scripts/selfcheck.py`로 확인한 뒤 `python tools/package_skill.py`로 배포본을 갱신한다. 기준 그림을 새로 만드는 일은 의도적으로 조판을 변경할 때에만 한다.
