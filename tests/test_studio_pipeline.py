import json
import os
import tempfile
import unittest
from src.storyboard_engine import build_storyboard
from src.jianying_draft_exporter import export_full_bundle


class TestMangaStudioPipeline(unittest.TestCase):
    def test_end_to_end_bundle_generation(self):
        sample = (
            "林玄冷笑一声，踏步走入青云大殿：“三年前你们夺我剑骨，今日我便讨回一切！”\n"
            "苏清雪脸色煞白，难以置信地后退半步：“你……你竟然从万魔渊活着出来了？！”"
        )
        sb = build_storyboard(sample, title="测试剧集_第1集", style_id="xianxia")
        self.assertGreaterEqual(sb["total_shots"], 2)
        self.assertGreaterEqual(len(sb["characters"]), 2)
        self.assertEqual(sb["characters"][0]["name"], "林玄")

        with tempfile.TemporaryDirectory() as tmpdir:
            paths = export_full_bundle(sb, tmpdir)
            self.assertTrue(os.path.exists(paths["storyboard_json"]))
            self.assertTrue(os.path.exists(paths["subtitles_srt"]))
            self.assertTrue(os.path.exists(paths["preview_html"]))
            self.assertTrue(os.path.exists(paths["draft_content_json"]))

            with open(paths["draft_content_json"], encoding="utf-8") as f:
                draft = json.load(f)
            self.assertEqual(draft["canvas_config"]["ratio"], "9:16")
            # We now have 4 tracks because of the new BGM track added by enrich_draft_content
            self.assertEqual(len(draft["tracks"]), 4)


if __name__ == "__main__":
    unittest.main()
