import unittest
import zipfile
import io
import json
from ultra_modules.batch_episode_zip_packager_core_engine import pack_episodes_to_zip

class TestBatchEpisodeZipPackagerCoreEngine(unittest.TestCase):
    def test_normal_execution(self):
        """测试正常包含完整数据的打包"""
        episodes = [
            {
                "episode_number": 1,
                "title": "Awakening",
                "mp4_content": b"real_mp4_data",
                "srt_content": "1\n00:00:01,000 --> 00:00:02,000\nHello",
                "draft_content": {"version": "2.0"},
                "prompts": "prompt1"
            },
            {
                "episode_number": 2,
                "title": "Journey",
                "mp4_content": "real_mp4_data_str",
                "srt_content": "1\n00:00:01,000 --> 00:00:02,000\nWorld",
                "draft_content": [{"track": 1}],
                "prompts": {"role": "hero"}
            }
        ]

        zip_bytes = pack_episodes_to_zip(episodes=episodes)
        self.assertIsInstance(zip_bytes, bytes)

        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
            files = zf.namelist()
            self.assertIn("Ep001_Awakening/video.mp4", files)
            self.assertIn("Ep001_Awakening/subtitles.srt", files)
            self.assertIn("Ep001_Awakening/draft_content.json", files)
            self.assertIn("Ep001_Awakening/prompts.txt", files)

            self.assertIn("Ep002_Journey/video.mp4", files)

            self.assertEqual(zf.read("Ep001_Awakening/video.mp4"), b"real_mp4_data")
            self.assertEqual(zf.read("Ep002_Journey/video.mp4"), b"real_mp4_data_str")

            draft_json = json.loads(zf.read("Ep002_Journey/draft_content.json").decode('utf-8'))
            self.assertEqual(draft_json, [{"track": 1}])

            prompts_json = json.loads(zf.read("Ep002_Journey/prompts.txt").decode('utf-8'))
            self.assertEqual(prompts_json, {"role": "hero"})

    def test_missing_parameters_fallback(self):
        """测试完全缺参兜底，即不传参数或传 None"""
        zip_bytes = pack_episodes_to_zip()
        self.assertIsInstance(zip_bytes, bytes)
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
            files = zf.namelist()
            self.assertIn("README.md", files)
            self.assertEqual(zf.read("README.md"), b"Empty Manga Drama Studio Archive - Auto Generated")

        zip_bytes2 = pack_episodes_to_zip(episodes=None)
        self.assertIsInstance(zip_bytes2, bytes)

    def test_dirty_data_self_healing(self):
        """测试脏数据自愈：传入非列表，或者列表中包含非字典元素"""
        # episodes是字典而不是列表
        episodes_dict = {"episode_number": 99, "title": "Lone Dict"}
        zip_bytes = pack_episodes_to_zip(episodes=episodes_dict)
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
            self.assertIn("Ep099_Lone_Dict/video.mp4", zf.namelist())

        # episodes是字符串等无效类型
        zip_bytes2 = pack_episodes_to_zip(episodes="invalid_string")
        with zipfile.ZipFile(io.BytesIO(zip_bytes2), 'r') as zf:
            self.assertIn("README.md", zf.namelist())

        # 列表中有脏数据
        dirty_episodes = [
            None,
            "string_instead_of_dict",
            123,
            {"title": "Valid One"}
        ]
        zip_bytes3 = pack_episodes_to_zip(episodes=dirty_episodes)
        with zipfile.ZipFile(io.BytesIO(zip_bytes3), 'r') as zf:
            files = zf.namelist()
            # 索引0 -> Ep001_Episode_1
            # 索引1 -> Ep002_Episode_2
            # 索引2 -> Ep003_Episode_3
            # 索引3 -> Ep004_Valid_One
            self.assertTrue(any(f.startswith("Ep001_Episode_1/") for f in files))
            self.assertTrue(any(f.startswith("Ep002_Episode_2/") for f in files))
            self.assertTrue(any(f.startswith("Ep003_Episode_3/") for f in files))
            self.assertTrue(any(f.startswith("Ep004_Valid_One/") for f in files))

    def test_extreme_boundary_cases(self):
        """测试极端边界：异常的集数、异常的标题字符"""
        episodes = [
            {
                "episode_number": "not_a_number",
                "title": "  !@#$%^&*()_+  ", # 全是非法字符
                "mp4_content": 12345, # 异常类型
                "srt_content": 12345, # 异常类型
                "draft_content": "not_a_dict_or_list",
            }
        ]
        zip_bytes = pack_episodes_to_zip(episodes=episodes)
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
            files = zf.namelist()
            # 集数非数字回退为 idx+1=1，title非法字符被过滤后如果是空则回退为 Episode_1
            self.assertTrue(any(f.startswith("Ep001_Episode_1/") for f in files))

            # 检查非法类型数据被清洗后的默认值
            self.assertEqual(zf.read("Ep001_Episode_1/video.mp4"), b"fake_mp4_header")
            self.assertEqual(zf.read("Ep001_Episode_1/subtitles.srt"), b"1\n00:00:00,000 --> 00:00:05,000\n[Auto-generated Subtitles]")
            draft_content = json.loads(zf.read("Ep001_Episode_1/draft_content.json").decode('utf-8'))
            self.assertEqual(draft_content, {"version": "1.0", "type": "auto-fallback-draft"})

    def test_output_path_file_generation(self):
        """测试指定 output_path 时生成文件"""
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "test.zip")
            res = pack_episodes_to_zip(episodes=[{"title": "File Test"}], output_path=out_file)
            self.assertTrue(res)
            self.assertTrue(os.path.exists(out_file))

            with zipfile.ZipFile(out_file, 'r') as zf:
                files = zf.namelist()
                self.assertTrue(any(f.startswith("Ep001_File_Test/") for f in files))

if __name__ == '__main__':
    unittest.main()
