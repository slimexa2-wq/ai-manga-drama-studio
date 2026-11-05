import os
import json
import zipfile
import tempfile
import unittest
from src.studio_packager import package_project, generate_style_comparison_html, create_zip_package


class TestStudioPackager(unittest.TestCase):
    def test_package_project(self):
        sample = (
            "林玄冷笑一声，踏步走入青云大殿：“三年前你们夺我剑骨，今日我便讨回一切！”\n"
            "苏清雪脸色煞白，难以置信地后退半步：“你……你竟然从万魔渊活着出来了？！”"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "test_project")
            paths, sb = package_project(sample, title="测试包_第1集", style_id="xianxia", output_dir=out_dir)

            self.assertIsNotNone(sb)
            # Check basic outputs
            self.assertTrue(os.path.exists(paths["storyboard_json"]))
            self.assertTrue(os.path.exists(paths["subtitles_srt"]))
            self.assertTrue(os.path.exists(paths["preview_html"]))
            self.assertTrue(os.path.exists(paths["draft_content_json"]))

            # Check new outputs
            self.assertTrue(os.path.exists(paths["style_comparison_html"]))
            self.assertTrue(os.path.exists(paths["zip_package"]))

            # Verify HTML content
            with open(paths["style_comparison_html"], "r", encoding="utf-8") as f:
                html_content = f.read()
            self.assertIn("8大画风一键对比预览", html_content)
            self.assertIn("国风修仙玄幻", html_content)
            self.assertIn("ChatGPT Plus (GPT-Image-2)", html_content)

            # Verify ZIP file
            zip_path = paths["zip_package"]
            self.assertTrue(zipfile.is_zipfile(zip_path))
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                namelist = zipf.namelist()
                # Assuming the root folder inside zip is named 'test_project'
                self.assertIn(f"test_project/storyboard.json", namelist)
                self.assertIn(f"test_project/style_comparison.html", namelist)
                self.assertIn(f"test_project/jianying_draft/draft_content.json", namelist)


if __name__ == "__main__":
    unittest.main()
