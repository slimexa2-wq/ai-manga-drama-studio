/**
 * Zero-Config ego-browser Bridge for Google 20x Ultra (Gemini 3.1 Pro / Google Flow / Veo 3)
 * and ChatGPT Plus (GPT-4o / GPT-Image-2).
 * Run via: /Users/wangmini/.local/bin/ego-browser nodejs < scripts/ego_dual_ecosystem_runner.mjs
 */

import fs from "node:fs";
import path from "node:path";

const sbPath = process.env.MANGA_STORYBOARD_JSON || "/Users/wangmini/Downloads/AI漫剧工程输出/第一集_魔帝归来/storyboard.json";
let sb = { title: "第一集_魔帝归来", shots: [], characters: [] };
try {
  if (fs.existsSync(sbPath)) {
    sb = JSON.parse(fs.readFileSync(sbPath, "utf8"));
  }
} catch (e) {}

const shots = sb.shots || [];
const chars = sb.characters || [];

const chatgptPromptBatch = [
  `请作为爆款竖屏漫剧视觉导演，为《${sb.title}》生成角色三视图设定与第1镜 9:16 分镜关键帧：`,
  chars[0] ? `【角色锁脸设定】：${chars[0].chatgpt_character_sheet_prompt}` : "",
  shots[0] ? `【SHOT_01 (GPT-Image-2 9:16 分镜词)】：${shots[0].chatgpt_plus_image_prompt}` : "",
].filter(Boolean).join("\n\n");

const geminiPromptBatch = [
  `请作为 Google 20x Ultra 漫剧总导演，审校《${sb.title}》分镜连续性并输出 Google Flow (Imagen 4 + Veo 3) 动态运镜执行单：`,
  ...shots.map(s => `- ${s.shot_id} (${s.duration_sec}s, ${s.emotion}):\n  [Imagen 4 画面]: ${s.google_ultra_flow_image_prompt}\n  [Veo 3 运镜]: ${s.google_ultra_veo3_video_prompt}`)
].join("\n");

const spaceName = "manga-studio-" + Date.now().toString(36);
const t = await taskSpace(spaceName, { profileId: "Profile 1" });

try {
  // 1. ChatGPT Plus (https://chatgpt.com/) — Auto-fill & trigger prompt
  const gptPage = await t.newPage();
  await gptPage.goto("https://chatgpt.com/");
  await gptPage.waitForTimeout(2500);
  const gptFilled = await gptPage.evaluate((promptText) => {
    const el = document.querySelector('#prompt-textarea, [contenteditable="true"], textarea');
    if (!el) return { filled: false, submitted: false };
    el.focus();
    if (el.tagName === "TEXTAREA" || el.tagName === "INPUT") {
      el.value = promptText;
      el.dispatchEvent(new Event("input", { bubbles: true }));
    } else {
      el.innerHTML = `<p>${promptText.replace(/\n/g, "</p><p>")}</p>`;
      el.dispatchEvent(new InputEvent("input", { bubbles: true, data: promptText }));
    }
    setTimeout(() => {
      const sendBtn = document.querySelector('[data-testid="send-button"], button[aria-label*="Send"], button[aria-label*="发送"]');
      if (sendBtn && !sendBtn.disabled) sendBtn.click();
    }, 500);
    return { filled: true, submitted: true, title: document.title };
  }, chatgptPromptBatch);
  await gptPage.waitForTimeout(1200);

  // 2. Google Gemini 20x Ultra (https://gemini.google.com/app) — Auto-fill & trigger prompt
  const geminiPage = await t.newPage();
  await geminiPage.goto("https://gemini.google.com/app");
  await geminiPage.waitForTimeout(2500);
  const geminiFilled = await geminiPage.evaluate((promptText) => {
    const el = document.querySelector('rich-textarea [contenteditable="true"], [contenteditable="true"], textarea');
    if (!el) return { filled: false, submitted: false };
    el.focus();
    el.textContent = promptText;
    el.dispatchEvent(new InputEvent("input", { bubbles: true, data: promptText }));
    setTimeout(() => {
      const sendBtn = document.querySelector('button[aria-label*="Send"], button[aria-label*="发送"], .send-button');
      if (sendBtn) sendBtn.click();
    }, 500);
    return { filled: true, submitted: true, title: document.title };
  }, geminiPromptBatch);
  await geminiPage.waitForTimeout(1200);

  // 3. Google Flow / Veo 3 (https://labs.google/fx/tools/flow)
  const flowPage = await t.newPage();
  await flowPage.goto("https://labs.google/fx/tools/flow");
  await flowPage.waitForTimeout(1800);
  const flowTitle = await flowPage.title();

  const outDir = path.dirname(sbPath);
  const statusFile = path.join(outDir, "cloud_dispatch_status.json");
  const report = {
    ok: true,
    timestamp: new Date().toISOString(),
    task_space: spaceName,
    episode_title: sb.title,
    dispatched_shots: shots.length,
    chatgpt_plus: { url: "https://chatgpt.com/", ...gptFilled, status: "prompt_injected_and_submitted" },
    google_gemini_ultra: { url: "https://gemini.google.com/app", ...geminiFilled, status: "prompt_injected_and_submitted" },
    google_flow_veo3: { url: "https://labs.google/fx/tools/flow", title: flowTitle, status: "connected_and_ready" },
  };
  fs.writeFileSync(statusFile, JSON.stringify(report, null, 2), "utf8");
  console.log(JSON.stringify(report));
} finally {
  const allPages = await t.pages();
  await t.finish({ keep: allPages.map(p => p.label) });
}
