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
 * 문제 쪽도 자동:
 *   <section class="problems" data-id="a01" data-title="TOPIC 적용문제" data-desc="설명 한두 줄" data-per="2">
 *     <div class="qitem" data-no="A·01" data-lv="2" data-src="원서 P14.7-6" data-topic="01">
 *       <div class="t">지문</div><div class="fig"><img …></div>
 *     </div> …
 *   </section>
 *   data-per="2" (기본): 한 쪽에 위·아래 2문제, 나머지는 풀이 공간
 *   data-per="4": 짧은 계산 문제용 2×2
 *   data-lv = 난이도 1~3, data-topic = 관련 TOPIC (PAGE 칸은 그 TOPIC 첫 쪽으로 자동)
 *   data-hint = 힌트 한 줄 (문제 칸 맨 아래, 막혔을 때만 보게 작게)
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
    pg.dataset.chapter = anchor.dataset.chapter;
    pg.dataset.chtitle = anchor.dataset.chtitle;
    pg.dataset.topic = topic.dataset.no;
    pg.dataset.topictitle = topic.dataset.title;
    const content = el("div", "content");
    content.style.height = CONTENT_H + "mm";
    if (first) {
      pg.appendChild(el("div", "topic-band", `${pg.dataset.chapter} &nbsp;${pg.dataset.chtitle}`));
      const no = topic.dataset.no;
      // 숫자가 아닌 번호(예: "해설" = 빠른 정답·해설 장)는 TOPIC 번호 없이 제목만
      const noHtml = /^\d/.test(no) ? `<span class="no">TOPIC <i>${no[0]}</i>${no.slice(1)}</span>` : "";
      content.appendChild(el("div", "topic-title", noHtml + topic.dataset.title));
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
      if (b.classList.contains("fn")) {
        placeFootnote(content, b);
        if (over(content)) {
          // 각주가 본문 높이를 줄여 참조 블록이 잘리면, 참조 블록과 각주를 다음 쪽으로 옮긴다
          b.remove();
          content.style.height = CONTENT_H + "mm";
          const carry = [];
          let last = content.lastElementChild;
          if (last) { carry.unshift(last); last = last.previousElementSibling; }
          while (last && (/^H[34]$/.test(last.tagName) || last.classList.contains("keep-next"))) {
            carry.unshift(last);
            last = last.previousElementSibling;
          }
          content = newPage(topic, false, anchor);
          carry.forEach((c) => content.appendChild(c));
          placeFootnote(content, b);
        }
        continue;
      }
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


  function qhead(it) {
    const d = it.dataset;
    const lv = parseInt(d.lv || "1", 10);
    const sq = [1, 2, 3].map((k) => `<i class="${k <= lv ? "on" : ""}"></i>`).join("");
    const no = d.no || "";
    const m = no.match(/^(.*?)(\d)(\d)$/);
    const noHtml = m ? `${m[1]}<i>${m[2]}</i>${m[3]}` : no;
    return el("div", "qh",
      `<div class="no">${noHtml}</div>` +
      `<div class="meta"><div class="r1"><span class="lv">${sq}</span>` +
      `<span class="rec">1회<span></span>2회<span></span></span>` +
      `<span class="srcR">${d.src ? "| " + d.src + " |" : ""}</span></div>` +
      `<div class="r2"><span class="k">PAGE</span><span class="v" data-qpage="${d.topic || ""}"></span>` +
      `<span class="k">TOPIC</span><span class="v">${d.topic || "–"}</span></div></div>`);
  }

  function layoutProblems(sec, anchor) {
    const per = parseInt(sec.dataset.per || "2", 10);
    const items = Array.from(sec.querySelectorAll(":scope > .qitem"));
    for (let i = 0; i < items.length; i += per) {
      const pg = el("section", `page qpage per${per}`);
      pg.dataset.chapter = sec.dataset.chapter;
      pg.dataset.chtitle = sec.dataset.chtitle;
      if (i === 0 && sec.dataset.id) pg.dataset.id = sec.dataset.id;
      pg.dataset.run = sec.dataset.title || "";
      const content = el("div", "content qcontent");
      content.style.height = CONTENT_H + "mm";
      if (i === 0) {
        content.appendChild(el("div", "qhead",
          `<div class="big">${sec.dataset.title || ""}</div>` +
          `<div class="desc"><b>${sec.dataset.title || ""}</b>${sec.dataset.desc || ""}</div>`));
      }
      const grid = el("div", "qgrid");
      items.slice(i, i + per).forEach((it) => {
        if (!it.querySelector(":scope > .qh")) it.insertBefore(qhead(it), it.firstChild);
        if (it.dataset.hint && !it.querySelector(":scope > .hint"))
          it.appendChild(el("div", "hint", `<b>힌트</b> ${it.dataset.hint}`));
        grid.appendChild(it);
      });
      content.appendChild(grid);
      pg.appendChild(content);
      anchor.parentNode.insertBefore(pg, anchor);
    }
    sec.remove();
  }

  function labelChapters() {
    let chapter = B.dataset.chapter || "";
    let title = B.dataset.chtitle || "";
    B.querySelectorAll(".page, article.manuscript, section.problems").forEach(node => {
      if (node.dataset.front) return;
      if (node.classList.contains("cover")) {
        chapter = node.dataset.chapter || B.dataset.chapter || "";
        title = node.dataset.chtitle || B.dataset.chtitle || "";
      }
      node.dataset.chapter ||= chapter;
      node.dataset.chtitle ||= title;
    });
  }

  // ---- Part 전체 차례 (한완수식: 장 | 항목 | 쪽) ----
  function tocLabel(pg) {
    const id = pg.dataset.id || "";
    if (pg.dataset.topic) {
      if (/^\d/.test(pg.dataset.topic)) return ["TOPIC " + pg.dataset.topic + ". " + pg.dataset.topictitle, ""];
      return [pg.dataset.topictitle, "sub"];
    }
    if (id === "preview") return ["Preview", "sub"];
    if (id === "review") return ["Review", "sub"];
    if (id) return [pg.dataset.run || id, "sub"];
    return null;
  }

  function makeBookContents() {
    const host = B.querySelector("[data-toc-host]");
    if (!host) return;
    const groups = [];
    let cur = null;
    const seen = new Set();
    for (const pg of B.querySelectorAll(".page:not([data-front])")) {
      if (pg.classList.contains("cover")) {
        cur = { name: [pg.dataset.chapter, pg.dataset.chtitle].filter(Boolean).join(". "), rows: [] };
        groups.push(cur);
        continue;
      }
      const lab = tocLabel(pg);
      if (!lab) continue;
      const key = (pg.dataset.chapter || "") + "/" + (pg.dataset.topic || pg.dataset.id);
      if (seen.has(key)) continue;
      seen.add(key);
      if (!cur) { cur = { name: "", rows: [] }; groups.push(cur); }
      cur.rows.push([lab[0], lab[1], pg]);
    }
    const guide = Array.from(B.querySelectorAll(".page[data-toc]"));
    if (guide.length) {
      const g = { name: "가이드라인", rows: [] };
      const done = new Set();
      guide.forEach((pg) => { if (!done.has(pg.dataset.toc)) { done.add(pg.dataset.toc); g.rows.push([pg.dataset.toc, "", pg]); } });
      groups.unshift(g);
    }
    let sheet = host, table = host.querySelector("table.btoc");
    const nums = [];
    const limit = () => sheet.getBoundingClientRect().bottom - 25 * MM;   // print.cjs 넘침 검사(24mm)보다 안쪽
    groups.forEach((g) => {
      g.rows.forEach(([label, cls, target], i) => {
        const tr = el("tr", (i === 0 ? "first " : "") + cls);
        const c1 = el("td", "c1", i === 0 ? g.name : "");
        const c2 = el("td", "it"); c2.textContent = label;
        const c3 = el("td", "pg");
        tr.append(c1, c2, c3);
        table.appendChild(tr);
        if (tr.getBoundingClientRect().bottom > limit() && table.rows.length > 1) {
          tr.remove();
          const next = host.cloneNode(true);
          next.removeAttribute("data-toc-host");
          next.querySelector(".btoc-head").remove();
          table = next.querySelector("table.btoc");
          table.replaceChildren();
          sheet.after(next);
          sheet = next;
          if (i > 0) { c1.textContent = g.name; tr.classList.add("first"); }
          table.appendChild(tr);
        }
        nums.push([c3, target]);
      });
    });
    const pages = Array.from(B.querySelectorAll(".page"));
    const start = Number(B.dataset.start || 1);
    nums.forEach(([c, t]) => { c.textContent = start + pages.indexOf(t); });
  }

  // ---- 앞부분: 묶음별로 넘치면 다음 쪽에 이어 붙인다 (첫 쪽에만 머리) ----
  function paginateFrontMatter() {
    for (const first of Array.from(B.querySelectorAll(".page.fmflow"))) {
      const body = first.querySelector(".fm-body");
      const items = Array.from(body.children);
      body.replaceChildren();
      let page = first, cur = body;
      const bottom = () => page.getBoundingClientRect().bottom - (page.classList.contains("nofoot") ? 20 : 26) * MM;
      for (const item of items) {
        cur.appendChild(item);
        if (item.getBoundingClientRect().bottom <= bottom() || cur.children.length === 1) continue;
        // 해법 박스는 단계 단위로 나눈다
        if (item.classList.contains("sol")) {
          const box = item.querySelector(":scope > .box");
          const moved = [];
          while (box && box.children.length > 1 && item.getBoundingClientRect().bottom > bottom()) {
            moved.unshift(box.lastElementChild); box.lastElementChild.remove();
          }
          if (moved.length && item.getBoundingClientRect().bottom <= bottom()) {
            const cont = el("div", item.className); cont.style.marginTop = "0";
            const cb = el("div", "box"); moved.forEach((m) => cb.appendChild(m)); cont.appendChild(cb);
            ({ page, cur } = nextFront(first, page));
            cur.appendChild(cont);
            continue;
          }
          moved.forEach((m) => box.appendChild(m));
        }
        item.remove();
        // 제목은 다음 블록과 함께 넘긴다
        const carry = [];
        let last = cur.lastElementChild;
        while (last && (/^H[34]$/.test(last.tagName) || last.classList.contains("keep-next") || last.classList.contains("fm-method"))) {
          carry.unshift(last); last = last.previousElementSibling;
        }
        ({ page, cur } = nextFront(first, page));
        carry.forEach((c) => cur.appendChild(c));
        cur.appendChild(item);
      }
    }
  }

  function nextFront(first, after) {
    const pg = first.cloneNode(false);
    pg.classList.add("cont");
    if (first.querySelector(".fm-head.guide")) pg.appendChild(el("div", "topline"));
    const body = el("div", "fm-body");
    pg.appendChild(body);
    after.after(pg);
    return { page: pg, cur: body };
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
      const numbered = topic && /^\d/.test(topic);
      if (odd && numbered && !pg.querySelector(".tab-topic")) pg.appendChild(el("div", "tab-topic", `TOPIC<b>${topic}</b>`));
      let foot = pg.querySelector(".foot");
      if (!foot) { foot = el("div", "foot"); pg.appendChild(foot); }
      let ttl;
      if (pg.dataset.run) ttl = pg.dataset.run;
      else if (odd && numbered) ttl = `<span class="t">TOPIC ${topic}</span>&nbsp; ${pg.dataset.topictitle}`;
      else if (topic && !numbered) ttl = `<span class="t">${pg.dataset.chapter}</span>&nbsp; ${pg.dataset.topictitle}`;
      else ttl = `<span class="t">${pg.dataset.chapter}</span>&nbsp; ${pg.dataset.chtitle}`;
      foot.innerHTML = `<span class="num">${n}</span><span class="bar"></span><span class="ttl">${ttl}</span>`;
    });
    // 문제 머리의 PAGE 칸: 관련 TOPIC 첫 쪽
    document.querySelectorAll("[data-qpage]").forEach((sp) => {
      const t = sp.dataset.qpage;
      const chapter = sp.closest(".page").dataset.chapter;
      const target = t && pages.find(p => p.dataset.topic === t && p.dataset.chapter === chapter);
      if (target) sp.textContent = start + pages.indexOf(target);
      else if (!sp.textContent) sp.textContent = "–";
    });
    // 목차 쪽 번호 자동 채우기: <td class="pg" data-ref="topic-01"> / data-ref="preview" 등
    document.querySelectorAll("[data-ref]").forEach((td) => {
      const ref = td.dataset.ref;
      let target = null;
      const chapter = td.closest(".page")?.dataset.chapter;
      target = pages.find(p => p.dataset.chapter === chapter && (ref.startsWith("topic-") ? p.dataset.topic === ref.slice(6) : p.dataset.id === ref));
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
    labelChapters();
    await waitAssets();
    document.querySelectorAll("article.manuscript").forEach((art) => {
      art.querySelectorAll(":scope > section.topic").forEach((t) => flowTopic(t, art));
      art.remove();
    });
    document.querySelectorAll("section.problems").forEach((sec) => layoutProblems(sec, sec));
    paginateFrontMatter();
    makeBookContents();
    decorate();
    B.setAttribute("data-ready", "1");
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run);
  else run();
})();
