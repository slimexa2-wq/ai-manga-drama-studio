import json

class DraftExplainer:
    def __init__(self):
        pass

    def explain(self, data, format_type='markdown'):
        """
        Translates complex Jianying Pro draft enrichment results into a plain language summary card.
        """
        # Data sanitization (dirty data self-healing and missing parameter fallback)
        if not isinstance(data, dict):
            data = {}

        effects = data.get('effects', [])
        if not isinstance(effects, list):
            effects = []

        transitions = data.get('transitions', [])
        if not isinstance(transitions, list):
            transitions = []

        camera_moves = data.get('camera_moves', [])
        if not isinstance(camera_moves, list):
            camera_moves = []

        bgm = data.get('bgm', None)
        if not isinstance(bgm, dict) and not isinstance(bgm, str):
            bgm = "无背景音乐"
        elif isinstance(bgm, dict):
            bgm = bgm.get('name', '默认背景音乐')

        if not bgm:
            bgm = "无背景音乐"

        # Parse content
        effects_summary = []
        for eff in effects:
            if isinstance(eff, dict) and 'name' in eff:
                effects_summary.append(eff['name'])
            elif isinstance(eff, str):
                effects_summary.append(eff)
        effects_text = "、".join(effects_summary) if effects_summary else "无特效"

        transitions_summary = []
        for trans in transitions:
            if isinstance(trans, dict) and 'name' in trans:
                transitions_summary.append(trans['name'])
            elif isinstance(trans, str):
                transitions_summary.append(trans)
        transitions_text = "、".join(transitions_summary) if transitions_summary else "无转场"

        camera_summary = []
        for cam in camera_moves:
            if isinstance(cam, dict) and 'name' in cam:
                camera_summary.append(cam['name'])
            elif isinstance(cam, str):
                camera_summary.append(cam)
        camera_text = "、".join(camera_summary) if camera_summary else "无运镜"

        # Generate output based on format
        format_type = str(format_type).lower() if isinstance(format_type, str) else 'markdown'
        if format_type not in ['markdown', 'html', 'json']:
            format_type = 'markdown'

        if format_type == 'json':
            return json.dumps({
                "总结卡片": {
                    "花字特效": effects_text,
                    "震屏转场": transitions_text,
                    "KenBurns运镜": camera_text,
                    "BGM注入": bgm
                }
            }, ensure_ascii=False, indent=2)

        elif format_type == 'html':
            return (
                "<div class='draft-summary-card'>\n"
                f"  <h3>剪映草稿效果大白话总结</h3>\n"
                f"  <p><strong>花字特效：</strong>{effects_text}</p>\n"
                f"  <p><strong>震屏转场：</strong>{transitions_text}</p>\n"
                f"  <p><strong>KenBurns运镜：</strong>{camera_text}</p>\n"
                f"  <p><strong>BGM注入：</strong>{bgm}</p>\n"
                "</div>"
            )

        else: # markdown
            return (
                "### 剪映草稿效果大白话总结\n\n"
                f"- **花字特效**：{effects_text}\n"
                f"- **震屏转场**：{transitions_text}\n"
                f"- **KenBurns运镜**：{camera_text}\n"
                f"- **BGM注入**：{bgm}\n"
            )
