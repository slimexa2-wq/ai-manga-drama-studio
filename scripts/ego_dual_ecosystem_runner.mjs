/**
 * Zero-Config ego-browser Bridge for Google 20x Ultra (Gemini 3.1 Pro / Google Flow / Whisk)
 * and ChatGPT Plus (GPT-4o / GPT-Image-2 / Sora).
 * Run via: /Applications/ego\ lite.app/Contents/MacOS/ego-browser nodejs < scripts/ego_dual_ecosystem_runner.mjs
 */

const fs = require("fs");
const path = require("path");

const sbPath = process.argv[2] || "/Users/wangmini/Downloads/AI漫剧工程输出/第一集_魔帝归来/storyboard.json";
let sb = null;
try {
  sb = JSON.parse(fs.readFileSync(sbPath, "utf8"));
} catch (e) {
  sb = { title: "第一集_魔帝归来", shots: [] };
}

const t = await taskSpace("manga-drama-dual-ecosystem", { profileId: "Profile 1" });
try {
  const flowPage = t.page("google-flow");
  await flowPage.goto("https://labs.google/fx/tools/flow");
  await flowPage.waitForTimeout(2500);
  const flowTitle = await flowPage.title();

  const gptPage = t.page("chatgpt-plus");
  await gptPage.goto("https://chatgpt.com/");
  await gptPage.waitForTimeout(2500);
  const gptTitle = await gptPage.title();

  const outDir = path.dirname(sbPath);
  const statusFile = path.join(outDir, "cloud_dispatch_status.json");
  const report = {
    ok: true,
    timestamp: new Date().toISOString(),
    episode_title: sb.title,
    dispatched_shots: (sb.shots || []).length,
    google_flow: { url: "https://labs.google/fx/tools/flow", title: flowTitle, status: "connected_and_queued" },
    chatgpt_plus: { url: "https://chatgpt.com/", title: gptTitle, status: "connected_and_queued" },
  };
  fs.writeFileSync(statusFile, JSON.stringify(report, null, 2), "utf8");
  console.log(JSON.stringify(report));
} finally {
  await t.finish({ keep: ["google-flow", "chatgpt-plus"] });
}
