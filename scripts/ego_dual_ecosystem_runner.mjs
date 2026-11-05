/**
 * Zero-Config ego-browser Bridge for Google 20x Ultra (Gemini 3.1 Pro / Google Flow / Whisk)
 * and ChatGPT Plus (GPT-4o / GPT-Image-2 / Sora).
 * Run via: ego-browser nodejs < scripts/ego_dual_ecosystem_runner.mjs
 */

const t = await taskSpace("manga-drama-dual-ecosystem", { profileId: "Profile 1" });
try {
  const page = t.page("p1");
  await page.goto("https://labs.google/fx/tools/flow");
  await page.waitForTimeout(3000);
  console.log("Connected to Google Labs Flow:", await page.title());
} finally {
  await t.finish({ keep: [] });
}
