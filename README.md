# 🎬 AI Manga Drama Studio (`ai-manga-drama-studio`)

**Google 20x AI Ultra (`Flow / Veo 3 / Whisk / Imagen 4 / Gemini 3.1 Pro`) × ChatGPT Plus (`GPT-4o / o3 / GPT-Image-2 / Sora`) 极简一键漫剧生产工作流**

## 核心设计第一性原理
> **效率优先，操作简单直观，后台复杂但前端极简，拒绝过度安全与繁琐配置！**
> - **前端零门槛**：1 个输入框粘贴小说/剧本 + 1 次点击，零登录墙、零安全令牌弹窗、零节点连线。
> - **后台全自动**：自动完成黄金前 3 秒钩子拆解、StoryDiffusion 级角色 DNA 锁脸卡、`awesome-gpt-image-2` 工业级双生态提示词编译、SRT 精确毫秒级字幕对齐、以及 **剪映专业版 (`draft_content.json`) 草稿工程一键生成**。

## 一键运行

```bash
# 1. 命令行一键生成全套漫剧工程包（输出至 ~/Downloads/AI漫剧工程输出/）
manga-studio run --title "第一集_魔帝归来" --style xianxia

# 2. 启动本地极简一键 Web 工作台 (http://127.0.0.1:8788)
manga-studio serve --port 8788
```
