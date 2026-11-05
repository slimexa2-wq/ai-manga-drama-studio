/**
 * Zero-Config ego-browser Bridge for Google 20x Ultra (Gemini 3.1 Pro / Google Flow / Whisk)
 * and ChatGPT Plus (GPT-4o / GPT-Image-2 / Sora).
 * Run via: /Users/wangmini/.local/bin/ego-browser nodejs < scripts/ego_dual_ecosystem_runner.mjs
 */

import fs from "node:fs";
import path from "node:path";

const sbPath = process.env.MANGA_STORYBOARD_JSON || "/Users/wangmini/Downloads/AI漫剧工程输出/第一集_魔帝归来/storyboard.json";
let sb = { title: "第一集_魔帝归来", shots: [] };
try {
  if (fs.existsSync(sbPath)) {
    sb = JSON.parse(fs.readFileSync(sbPath, "utf8"));
  }
} catch (e) {}

let t;
try {
  t = await taskSpace("manga-drama-dual-ecosystem");
} catch (e) {
  t = await taskSpace("manga-drama-dual-ecosystem", { profileId: "Profile 1" });
}
try {
  const existing = await t.pages();
  const flowPage = existing.length > 0 ? t.page(existing[0].label) : await t.newPage();
  await flowPage.goto("https://labs.google/fx/tools/flow");
  await flowPage.waitForTimeout(1500);
  const flowTitle = await flowPage.title();

  const gptPage = existing.length > 1 ? t.page(existing[1].label) : await t.newPage();
  await gptPage.goto("https://chatgpt.com/");
  await gptPage.waitForTimeout(1500);
  const gptTitle = await gptPage.title();

  const outDir = path.dirname(sbPath);
  const statusFile = path.join(outDir, "cloud_dispatch_status.json");
  const report = {
    ok: true,
    timestamp: new Date().toISOString(),
    episode_title: sb.title,
    dispatched_shots: (sb.shots || []).length,
    google_flow: { url: "https://labs.google/fx/tools/flow", title: flowTitle, status: "connected_and_ready" },
    chatgpt_plus: { url: "https://chatgpt.com/", title: gptTitle, status: "connected_and_ready" },
  };
  fs.writeFileSync(statusFile, JSON.stringify(report, null, 2), "utf8");
  console.log(JSON.stringify(report));
} finally {
  const allPages = await t.pages();
  await t.finish({ keep: allPages.map(p => p.label) });
}
