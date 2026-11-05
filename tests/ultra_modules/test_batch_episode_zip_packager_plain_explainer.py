import unittest
import os
import shutil
import tempfile
from ultra_modules.batch_episode_zip_packager_plain_explainer import BatchEpisodeZipPackagerPlainExplainer

class TestBatchEpisodeZipPackagerPlainExplainer(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.packager = BatchEpisodeZipPackagerPlainExplainer(output_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_01_normal_execution(self):
        """测试正常执行：完整数据，应生成包含所有报告的返回和zip文件"""
        # 准备假文件
        ep1_mp4 = os.path.join(self.test_dir, "ep1.mp4")
        with open(ep1_mp4, "w") as f: f.write("video")

        batch_data = [
            {
                "episode": 1,
                "mp4": ep1_mp4,
                "srt": "",
                "draft": "",
                "prompts": "",
                "status": "success"
            }
        ]

        result = self.packager.package(batch_data)

        self.assertTrue(result["success"])
        self.assertTrue(os.path.exists(result["zip_path"]))
        self.assertTrue(os.path.exists(result["md_path"]))
        self.assertTrue(os.path.exists(result["html_path"]))
        self.assertTrue(os.path.exists(result["json_path"]))

        self.assertIn("总计处理**：1 集", result["report_md"])
        self.assertIn("成功**：1 集", result["report_md"])

    def test_02_missing_parameters_fallback(self):
        """测试缺参兜底：缺失状态、部分文件，应自动推断并降级处理"""
        # 没有提供状态，只有 MP4 和 SRT，并且 episode 没有提供
        batch_data = [
            {
                "mp4": "dummy.mp4",
                "srt": "dummy.srt"
            }
        ]

        result = self.packager.package(batch_data)

        self.assertTrue(result["success"])
        self.assertIn("第 1 集", result["report_md"]) # 自动兜底episode
        self.assertIn("✅", result["report_md"])       # 自动推断为成功

    def test_03_dirty_data_self_healing(self):
        """测试脏数据自愈：异常的非字典格式、非法文件类型"""
        # batch_data 既不是 list 也不是 dict，且含有 None 和 乱码
        batch_data = "This is a dirty string instead of list"

        result = self.packager.package(batch_data)
        self.assertTrue(result["success"]) # 空操作也算成功
        self.assertIn("总计处理**：0 集", result["report_md"])

        # 列表内含有乱码
        batch_data_2 = [
            "wrong string",
            123,
            {"episode": 1, "status": "failed"},
            None
        ]

        result2 = self.packager.package(batch_data_2)
        # 应只解析出1个有效的（第三个元素），尽管它状态是failed
        self.assertIn("总计处理**：1 集", result2["report_md"])
        self.assertIn("失败**：1 集", result2["report_md"])

    def test_04_extreme_boundary_empty(self):
        """测试极端边界：空列表，或全空字段"""
        batch_data = []
        result = self.packager.package(batch_data)
        self.assertTrue(result["success"])
        self.assertIn("未发现任何集数数据", result["report_md"])

        batch_data_nulls = [
            {"episode": None, "mp4": None, "srt": None, "draft": None, "prompts": None, "status": None}
        ]
        result_nulls = self.packager.package(batch_data_nulls)
        self.assertFalse(result_nulls["success"]) # 没任何产物，应推断为失败
        self.assertIn("失败**：1 集", result_nulls["report_md"])

    def test_05_draft_folder_packaging(self):
        """测试目录打包：模拟剪映草稿目录"""
        draft_dir = os.path.join(self.test_dir, "draft_proj")
        os.makedirs(draft_dir)
        with open(os.path.join(draft_dir, "draft_content.json"), "w") as f:
            f.write("{}")

        batch_data = [
            {
                "episode": 1,
                "draft": draft_dir
            }
        ]

        result = self.packager.package(batch_data)
        self.assertTrue(result["success"])
        self.assertTrue(os.path.exists(result["zip_path"]))

        # 检查 zip 内是否包含草稿文件
        import zipfile
        with zipfile.ZipFile(result["zip_path"], 'r') as zipf:
            namelist = zipf.namelist()
            self.assertTrue(any("draft_content.json" in name for name in namelist))

if __name__ == '__main__':
    unittest.main()
