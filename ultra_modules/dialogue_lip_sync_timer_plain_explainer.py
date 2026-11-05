import json
import re

class DialogueLipSyncTimerPlainExplainer:
    def __init__(self, text=None, audio_peaks=None):
        # Zero-configuration fallback for text
        self.text = text if isinstance(text, str) else ""

        # Audio peaks fallback: handle None or invalid types by defaulting to empty list
        if not isinstance(audio_peaks, (list, tuple)):
            self.audio_peaks = []
        else:
            self.audio_peaks = [p for p in audio_peaks if isinstance(p, (int, float))]

    def calculate_duration_ms(self):
        # Text based duration
        # Assuming ~250ms per character (letters/numbers/chinese chars)
        char_count = len(re.sub(r'[^\w\u4e00-\u9fff]', '', self.text))
        text_dur = char_count * 250

        # Punctuation pauses
        comma_count = len(re.findall(r'[,，、]', self.text))
        period_count = len(re.findall(r'[.。!！?？;；]', self.text))

        text_dur += comma_count * 300 + period_count * 500

        # Default minimum duration 1000ms if there's text
        if self.text and text_dur < 1000:
            text_dur = 1000

        # Audio based duration
        audio_dur = 0
        if self.audio_peaks:
            audio_dur = max(self.audio_peaks) + 500 # 500ms buffer after last peak

        final_dur = max(text_dur, audio_dur)

        return {
            "text_duration_ms": text_dur,
            "audio_duration_ms": audio_dur,
            "final_duration_ms": final_dur,
            "char_count": char_count,
            "comma_count": comma_count,
            "period_count": period_count,
            "peak_count": len(self.audio_peaks)
        }

    def export(self, export_format='markdown'):
        # Fallback to markdown if invalid format
        if not isinstance(export_format, str) or export_format.lower() not in ['markdown', 'html', 'json']:
            export_format = 'markdown'

        export_format = export_format.lower()
        stats = self.calculate_duration_ms()

        # Simple plain explainer language
        conclusion = (
            f"根据分析，这段台词包含 {stats['char_count']} 个字，"
            f"以及 {stats['comma_count']} 个短停顿和 {stats['period_count']} 个长停顿。\n"
            f"预估纯文本朗读时长约 {stats['text_duration_ms'] / 1000:.2f} 秒。"
        )

        if stats['peak_count'] > 0:
            conclusion += f"\n检测到 {stats['peak_count']} 个音频波形峰值，音频对齐后要求最小时长为 {stats['audio_duration_ms'] / 1000:.2f} 秒。"

        conclusion += f"\n\n👉 最终建议该分镜最少保留时长为：{stats['final_duration_ms'] / 1000:.2f} 秒。"

        if export_format == 'json':
            return json.dumps({
                "conclusion": conclusion,
                "details": stats
            }, ensure_ascii=False, indent=2)
        elif export_format == 'html':
            return f"""<div class="sync-card">
  <h3>分镜时长建议卡</h3>
  <p>{conclusion.replace(chr(10), '<br>')}</p>
</div>"""
        else: # markdown
            return f"### 分镜时长建议卡\n\n{conclusion}"


def generate_sync_card(text=None, audio_peaks=None, export_format='markdown'):
    """
    Frontend 1-click helper function.
    """
    explainer = DialogueLipSyncTimerPlainExplainer(text=text, audio_peaks=audio_peaks)
    return explainer.export(export_format=export_format)
