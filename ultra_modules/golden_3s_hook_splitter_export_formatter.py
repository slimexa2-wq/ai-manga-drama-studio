import math

class Golden3sHookSplitterExportFormatter:
    @staticmethod
    def split_and_format(text=None, target_episodes=None):
        if not isinstance(text, str):
            text = ""

        if not isinstance(target_episodes, int) or target_episodes < 1:
            target_episodes = 1

        text = text.strip()
        total_words = len(text)

        episodes = []

        if total_words == 0:
            for i in range(target_episodes):
                episodes.append({
                    "episode_number": i + 1,
                    "content": "",
                    "word_count": 0,
                    "hook": "",
                    "suspense": ""
                })
        else:
            chunk_size = math.ceil(total_words / target_episodes)
            for i in range(target_episodes):
                start_idx = i * chunk_size
                end_idx = min((i + 1) * chunk_size, total_words)

                chunk = text[start_idx:end_idx]

                hook = chunk[:15] if len(chunk) > 15 else chunk
                suspense = chunk[-15:] if len(chunk) > 15 else chunk

                episodes.append({
                    "episode_number": i + 1,
                    "content": chunk,
                    "word_count": len(chunk),
                    "hook": hook,
                    "suspense": suspense
                })

        hook_text = episodes[0]["hook"] if episodes and episodes[0]["hook"] else "无"
        suspense_text = episodes[-1]["suspense"] if episodes and episodes[-1]["suspense"] else "无"

        summary = (
            f"📊 拆解汇报：总计 {total_words} 字，已拆分为 {target_episodes} 集。\n"
            f"🔥 黄金3秒钩子：{hook_text}\n"
            f"🎬 集末悬念卡点：{suspense_text}"
        )

        return {
            "comments": 0,
            "total_words": total_words,
            "target_episodes": target_episodes,
            "episodes": episodes,
            "summary": summary
        }
