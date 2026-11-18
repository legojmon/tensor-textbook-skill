/* Tensor 자동 쪽 나눔 엔진
 *
 * 원고는 쪽을 신경 쓰지 않고 한 줄로 길게 쓴다:
 *   <article class="manuscript">
 *     <section class="topic" data-no="01" data-title="응답식에서 회로 읽기"> …블록들… </section>
 *   </article>
 * 고정 쪽(표지, 목차, Preview, 문제 페이지)은 <section class="page …"> 로 직접 쓴다.
 *
 * <body> 속성: data-chapter="14" data-chtitle="라플라스 변환" data-part="Part2" data-start="16"
 *   data-start = 첫 .page(표지)의 쪽 번호
 *
 * 하는 일
 *  1. KaTeX 렌더 → 글꼴·그림 로딩 대기
 *  2. TOPIC 블록을 A4 쪽에 채워 넣고, 넘치면 다음 쪽으로
 *     - .sol 해법 박스는 단계(.step 등) 단위로 쪼개 다음 쪽에 라벨 없이 이어 붙임
 *     - h3/h4/.keep-next 는 다음 블록과 같은 쪽에 붙임
 *     - .fn 각주는 그 쪽 아래로 보내고 본문 높이를 줄임
 *     - <div class="pagebreak"></div> 는 강제 쪽 넘김
 *  3. 모든 쪽에 쪽 번호·짝/홀·꼬리말·Part/TOPIC 탭 부착
 *  4. body[data-ready="1"] 설정 (render.py 가 이 신호를 기다림)
 */
(function () {
  const MM = 96 / 25.4;
  const CONTENT_H = 253;            // mm: 297 - 위 20 - 아래 24

  let B, CH, CHT, PART;   // <head>에서 로드되므로 body 값은 run() 에서 읽는다

  function el(tag, cls, html) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html !== undefined) e.innerHTML = html;
    return e;
  }
  const over = (c) => c.scrollHeight > c.clientHeight + 1;

  function newPage(topic, first, anchor) {
    const pg = el("section", "page flowpage");
    pg.dataset.topic = topic.dataset.no;
    pg.dataset.topictitle = topic.dataset.title;
    const content = el("div", "content");
    content.style.height = CONTENT_H + "mm";
    if (first) {
      pg.appendChild(el("div", "topic-band", `${CH} &nbsp;${CHT}`));
      const no = topic.dataset.no;
      content.appendChild(el("div", "topic-title",
        `<span class="no">TOPIC <i>${no[0]}</i>${no.slice(1)}</span>${topic.dataset.title}`));
    } else {
      pg.appendChild(el("div", "topline"));
    }
    pg.appendChild(content);
    anchor.parentNode.insertBefore(pg, anchor);
    return content;
  }

  function placeFootnote(content, fn) {
    const pg = content.parentNode;
    pg.appendChild(fn);
    const h = fn.getBoundingClientRect().height / MM;
    content.style.height = (CONTENT_H - h - 4) + "mm";
  }

  function splitSol(sol, content, nextContent) {
    // sol 이 content 를 넘칠 때: 뒤쪽 단위를 새 박스로 옮긴다. 성공하면 새 박스를 돌려준다.
    const box = sol.querySelector(":scope > .box");
    if (!box) return null;
    const units = Array.from(box.children);
    if (units.length < 2) return null;
    const cont = el("div", sol.className);
    cont.style.marginTop = "0";
    const cbox = el("div", "box");
    cbox.style.marginTop = "0";
    cont.appendChild(cbox);
    while (over(content) && box.children.length > 1) {
      cbox.insertBefore(box.lastElementChild, cbox.firstChild);
    }
    if (over(content)) {               // 한 단위도 안 들어감 → 통째로 넘김
      while (cbox.firstChild) box.appendChild(cbox.firstChild);
      return null;
    }
    nextContent.appendChild(cont);
    return cont;
  }

  function flowTopic(topic, anchor) {
    const blocks = Array.from(topic.children);
    let content = newPage(topic, true, anchor);
    for (let i = 0; i < blocks.length; i++) {
      const b = blocks[i];
      if (b.classList.contains("pagebreak")) { content = newPage(topic, false, anchor); continue; }
      if (b.classList.contains("fn")) { placeFootnote(content, b); continue; }
      content.appendChild(b);
      if (!over(content)) continue;

      // 넘침 처리
      if (b.classList.contains("sol")) {
        const next = newPage(topic, false, anchor);
        const cont = splitSol(b, content, next);
        if (cont) { content = next; continue; }
        next.parentNode.remove();
      }
      content.removeChild(b);
      const prevContent = content;
      content = newPage(topic, false, anchor);
      // keep-with-next: 앞 쪽 끝의 제목/연결 문단을 함께 데려온다
      const carry = [];
      let last = prevContent.lastElementChild;
      while (last && (/^H[34]$/.test(last.tagName) || last.classList.contains("keep-next"))) {
        carry.unshift(last);
        last = last.previousElementSibling;
      }
      carry.forEach((c) => content.appendChild(c));
      content.appendChild(b);
      if (over(content)) console.warn("[tensor] 한 쪽보다 큰 블록:", b.className || b.tagName);
    }
  }

  function decorate() {
    const start = parseInt(B.dataset.start || "1", 10);
    const pages = Array.from(document.querySelectorAll(".page"));
    pages.forEach((pg, i) => {
      const n = start + i;
      const odd = n % 2 === 1;
      pg.classList.remove("odd", "even");
      pg.classList.add(odd ? "odd" : "even");
      if (pg.classList.contains("cover") || pg.classList.contains("toc") || pg.classList.contains("nofoot")) return;
      const topic = pg.dataset.topic;
      if (odd && !pg.querySelector(".tab-part")) pg.appendChild(el("div", "tab-part", PART));
      if (odd && topic && !pg.querySelector(".tab-topic")) pg.appendChild(el("div", "tab-topic", `TOPIC<b>${topic}</b>`));
      let foot = pg.querySelector(".foot");
      if (!foot) { foot = el("div", "foot"); pg.appendChild(foot); }
      let ttl;
      if (pg.dataset.run) ttl = pg.dataset.run;
      else if (odd && topic) ttl = `<span class="t">TOPIC ${topic}</span>&nbsp; ${pg.dataset.topictitle}`;
      else ttl = `<span class="t">${CH}</span>&nbsp; ${CHT}`;
      foot.innerHTML = `<span class="num">${n}</span><span class="bar"></span><span class="ttl">${ttl}</span>`;
    });
    // 목차 쪽 번호 자동 채우기: <td class="pg" data-ref="topic-01"> / data-ref="preview" 등
    document.querySelectorAll("[data-ref]").forEach((td) => {
      const ref = td.dataset.ref;
      let target = null;
      if (ref.startsWith("topic-")) target = document.querySelector(`.flowpage[data-topic="${ref.slice(6)}"]`);
      else target = document.querySelector(`.page[data-id="${ref}"]`);
      if (target) {
        const idx = Array.from(document.querySelectorAll(".page")).indexOf(target);
        td.textContent = start + idx;
      }
    });
  }

  async function waitAssets() {
    if (window.renderMathInElement) {
      renderMathInElement(document.body, {
        delimiters: [{ left: "$$", right: "$$", display: true }, { left: "$", right: "$", display: false }],
        throwOnError: false,
      });
    }
    await document.fonts.ready;
    await Promise.all(Array.from(document.images).map((im) =>
      im.complete ? Promise.resolve() : new Promise((r) => { im.onload = im.onerror = r; })));
  }

  async function run() {
    B = document.body;
    CH = B.dataset.chapter || "";
    CHT = B.dataset.chtitle || "";
    PART = B.dataset.part || "Part2";
    await waitAssets();
    document.querySelectorAll("article.manuscript").forEach((art) => {
      art.querySelectorAll(":scope > section.topic").forEach((t) => flowTopic(t, art));
      art.remove();
    });
    decorate();
    B.setAttribute("data-ready", "1");
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run);
  else run();
})();
