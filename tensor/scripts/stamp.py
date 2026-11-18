"""build.py 도장 — 빌더가 만든 원고인지, 만든 뒤 손으로 고치지 않았는지 확인한다.

build.py 가 HTML 을 다 만든 뒤 내용의 SHA-256 을 <meta name="tensor-build"> 로 붙인다(seal).
render.py 와 lint.py 는 도장을 다시 계산해 맞지 않으면 조판하지 않는다(verify).
frontmatter.py 처럼 원고를 바꾸는 공식 스크립트는 도장이 맞는 원고에만 작업하고 다시 도장을 찍는다.
줄바꿈(CRLF/LF) 차이는 같은 내용으로 본다.
"""
import hashlib
import re

MARK = re.compile(r'\n?<meta name="tensor-build" content="([0-9a-f]{64})">')
ANCHOR = '<meta charset="utf-8">'
HOWTO_FIX = ("이 파일은 build.py 가 만든 그대로가 아니다. HTML 을 손으로 쓰거나 고치지 않는다. "
             "work/book.json 을 고친 뒤 build.py 로 다시 만든다(앞부분은 그 뒤에 frontmatter.py).")


def _digest(text):
    body = MARK.sub("", text.replace("\r\n", "\n"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def seal(text):
    text = MARK.sub("", text.replace("\r\n", "\n"))
    if ANCHOR not in text:
        raise ValueError(f"도장을 찍을 자리({ANCHOR})가 없다")
    return text.replace(ANCHOR, f'{ANCHOR}\n<meta name="tensor-build" content="{_digest(text)}">', 1)


def verify(text):
    """(맞음, 이유) — 이유는 사용자에게 보여 줄 한 줄."""
    found = MARK.findall(text)
    if not found:
        return False, "build.py 도장이 없다. " + HOWTO_FIX
    if len(found) > 1:
        return False, "build.py 도장이 둘 이상이다. " + HOWTO_FIX
    if found[0] != _digest(text):
        return False, "build.py 도장과 내용이 다르다(만든 뒤 손으로 고침). " + HOWTO_FIX
    return True, ""
