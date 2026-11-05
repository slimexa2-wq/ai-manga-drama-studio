"""
Industrial visual style presets integrating awesome-gpt-image-2 style library
with Google 20x Ultra (Flow / Veo 3 / Whisk / Imagen 4) and ChatGPT Plus (GPT-Image-2 / Sora).
"""

STYLE_PRESETS = {
    "xianxia": {
        "id": "xianxia",
        "name": "🔥 国风修仙玄幻 (Xianxia / Cultivation)",
        "gpt_image_template": "Chinese Fantasy Illustration / Guofeng Celia & Ink Glow",
        "style_anchor": (
            "masterpiece Chinese xianxia anime style, cel-shaded with ethereal ink-wash glow, "
            "flowing silk hanfu robes, dramatic volumetric spiritual qi lighting, cinematic 9:16 vertical composition, "
            "ultra-detailed facial features, ufotable and Makoto Shinkai inspired lighting"
        ),
        "veo_motion_style": "smooth cinematic camera movement, floating silk and glowing particles in slow motion, 24fps anime film aesthetic",
        "default_bgm_mood": "epic_guzheng_orchestral",
    },
    "urban_counterattack": {
        "id": "urban_counterattack",
        "name": "⚡ 都市战神/逆袭爽剧 (Urban Counterattack)",
        "gpt_image_template": "High-Contrast Webtoon / Modern Noir Manhwa",
        "style_anchor": (
            "premium Korean webtoon manhwa style, sharp dynamic line art, dramatic rim lighting, "
            "modern luxury urban setting, intense emotional facial expressions, 9:16 vertical framing, "
            "rich contrast, Solo Leveling art quality"
        ),
        "veo_motion_style": "dramatic fast push-in camera zoom on character eyes, subtle hair and coat wind motion, high tension",
        "default_bgm_mood": "phonk_bass_tension",
    },
    "k_chaebol": {
        "id": "k_chaebol",
        "name": "🌸 唯美韩漫财阀/豪门甜虐 (Chaebol Romance)",
        "gpt_image_template": "Romantic K-Webtoon / Soft Bokeh Manhwa",
        "style_anchor": (
            "delicate Korean romance manhwa illustration, soft pastel and golden hour lighting, "
            "sparkling expressive eyes, haute couture fashion, dreamy bokeh background, 9:16 vertical portrait"
        ),
        "veo_motion_style": "gentle slow pan, soft light flares, subtle micro-expressions and blinking, romantic pacing",
        "default_bgm_mood": "emotional_piano_strings",
    },
    "shonen_battle": {
        "id": "shonen_battle",
        "name": "🗡️ 热血日漫少年/高燃战斗 (Shonen Action)",
        "gpt_image_template": "Dynamic Shonen Keyframe / MAPPA & Ufotable Style",
        "style_anchor": (
            "high-octane Japanese shonen anime keyframe, MAPPA and ufotable production quality, "
            "bold impact lines, dynamic foreshortening perspective, vibrant energy effects, 9:16 vertical"
        ),
        "veo_motion_style": "dynamic tracking shot, high-speed camera shake on impact, glowing particle burst",
        "default_bgm_mood": "rock_symphonic_battle",
    },
    "chinese_horror": {
        "id": "chinese_horror",
        "name": "👁️ 中式规则怪谈/悬疑反转 (Chinese Mystery & Folklore)",
        "gpt_image_template": "Atmospheric Cthulhu & Chinese Folklore Thriller",
        "style_anchor": (
            "eerie Chinese folklore suspense comic style, cold cyan and crimson paper-lantern contrast, "
            "misty atmospheric shadows, psychological thriller framing, uncanny detail, 9:16 vertical"
        ),
        "veo_motion_style": "slow creeping dolly-in, flickering red lantern light, unsettling subtle background movement",
        "default_bgm_mood": "suspense_heartbeat_erhu",
    },
    "cyberpunk": {
        "id": "cyberpunk",
        "name": "🤖 赛博朋克末日/机甲觉醒 (Cyberpunk Sci-Fi)",
        "gpt_image_template": "Neon Cyberpunk Anime / Edgerunners Aesthetic",
        "style_anchor": (
            "Studio Trigger Cyberpunk Edgerunners anime style, rain-slicked neon streets, "
            "holographic HUD reflections, chromatic aberration accents, 9:16 vertical cinematic frame"
        ),
        "veo_motion_style": "cybernetic glitch transition, neon light reflections moving across visor, parallax camera pan",
        "default_bgm_mood": "synthwave_cyber_bass",
    },
    "palace_intrigue": {
        "id": "palace_intrigue",
        "name": "👑 古风宫斗/重生复仇 (Ancient Palace Revenge)",
        "gpt_image_template": "Classical Chinese Court Manhua / Exquisite Finery",
        "style_anchor": (
            "exquisite ancient Chinese palace manhua style, ornate gold hairpins and embroidered robes, "
            "candlelit warm-cold contrast, sharp calculating gaze, architectural depth, 9:16 vertical"
        ),
        "veo_motion_style": "slow regal camera push-in, flickering candlelight, snow or cherry blossoms falling in foreground",
        "default_bgm_mood": "ancient_pipa_tension",
    },
    "cg_3d_donghua": {
        "id": "cg_3d_donghua",
        "name": "🎬 3D国漫电影级CG (3D Donghua Unreal Engine 5)",
        "gpt_image_template": "3D Donghua Cinema / Unreal Engine 5 Subsurface Scattering",
        "style_anchor": (
            "3D Chinese donghua movie quality rendered in Unreal Engine 5, realistic skin subsurface scattering, "
            "individual hair strands, cinematic depth of field, ray-traced lighting, 9:16 vertical"
        ),
        "veo_motion_style": "fluid 3D cinema camera orbit, realistic cloth and hair physics, shallow depth of field focus pull",
        "default_bgm_mood": "cinematic_epic_trailer",
    },
}


def get_style_preset(style_id: str) -> dict:
    return STYLE_PRESETS.get(style_id, STYLE_PRESETS["xianxia"])
