// One Chromium process renders all the sheets in a job with the same print settings.
const fs = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

async function print(job) {
  const { chromium } = require(path.join(job.build, "node_modules", "playwright-core"));
  const executablePath = process.env.TENSOR_CHROME ||
    (fs.existsSync(chromium.executablePath()) ? chromium.executablePath() : job.systemChrome);
  const browser = await chromium.launch({ executablePath: executablePath || undefined });
  try {
    for (const sheet of job.sheets) {
      const page = await browser.newPage({ viewport: { width: 900, height: 1200 } });
      const errors = [];
      page.on("pageerror", error => errors.push(error.message));
      page.on("requestfailed", req => errors.push(req.failure()?.errorText + " " + req.url()));
      page.on("console", msg => {
        if (["error", "warning"].includes(msg.type())) errors.push(msg.text());
      });
      await page.goto(pathToFileURL(sheet.html).href, { waitUntil: "load" });
      if (sheet.body) await page.waitForSelector("body[data-ready='1']", { timeout: 30000 });
      await page.evaluate(() => document.fonts.ready);
      const issues = await page.evaluate(({ body }) => {
        const problems = [];
        for (const img of document.images) if (!img.naturalWidth) problems.push("그림 로딩 오류: " + img.src);
        if (document.querySelector(".katex-error")) problems.push("수식 파싱 오류");
        if (!body) return problems;
        let index = 0;
        for (const pg of document.querySelectorAll(".page")) {
          index++;
          const limit = pg.getBoundingClientRect().bottom - 24 * 96 / 25.4;
          const nodes = pg.querySelectorAll("p,.step,.sol,.concept,.core,.tip,.grade,.vs,.ex,.fig,.qitem,table,.katex-display,.fm-body > *");
          const over = [...nodes].filter(n => !n.closest(".foot,.fn,.cover,.toc") && n.getBoundingClientRect().bottom > limit + 1);
          if (over.length) problems.push(index + "쪽 본문 넘침");
        }
        return problems;
      }, sheet);
      errors.push(...issues);
      for (const error of errors) console.error("[검수]", error);
      if (job.strict && errors.length) throw new Error("PDF 조판 검수 실패");
      await page.pdf({ path: sheet.pdf, preferCSSPageSize: true, printBackground: true });
      console.log(path.basename(sheet.pdf) + " · Chromium " + browser.version() + " · 검수 " + errors.length + "건");
      await page.close();
    }
  } finally {
    await browser.close();
  }
}
print(JSON.parse(fs.readFileSync(0, "utf8"))).catch(error => {
  console.error(error.message);
  process.exitCode = 1;
});
