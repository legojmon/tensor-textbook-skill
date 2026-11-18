---
name: tensor
description: 강의록·원서 PDF로 TENSOR 시험 대비 교재, 서문, 전체 목차, 내지와 표지 PDF를 제작하거나 Claude와 Codex의 조판 결과를 검증한다.
---

# TENSOR 교재 제작

이 파일에서 세 단계 위가 저장소 루트다. 루트의 `tensor/SKILL.md`를 읽고 그 지침과 참조 문서에 따라 작업한다. `<skill>`은 이 진입점이 아니라 루트의 `tensor/`를 가리킨다. 모든 명령은 같은 Python 환경에서 실행한다. 견본 조판 비교만 요청받으면 `python tensor/scripts/selfcheck.py`를 실행한다.

원고는 `work/book.json` 에 글만 쓰고 `python tensor/scripts/build.py work/book.json` 으로 조판한다(형식: `tensor/references/manuscript-schema.md`, 견본: `tensor/references/example-manuscript.json`). HTML·CSS 를 직접 쓰지 않는다. 전달 전 `build.py` 오류 0, `lint.py` 경고 0, `render.py --strict` 검수 0 을 확인한다.
