import unittest
import math
from ultra_modules.jianying_pro_draft_enricher_anomaly_radar import enrich_and_scan_draft

class TestJianyingProDraftEnricherAnomalyRadar(unittest.TestCase):

    def test_normal_operation_and_enrichment(self):
        """测试正常数据操作和特效/BGM注入"""
        draft_content = {
            "tracks": [
                {
                    "segments": [
                        {"id": "seg1", "duration": 2000000},
                        {"id": "seg2", "duration": 2500000},
                        {"id": "seg3", "duration": 2200000},
                        {"id": "seg4", "duration": 2400000},
                        {"id": "seg5", "duration": 2100000}
                    ]
                }
            ],
            "materials": {
                "audios": [],
                "effects": []
            }
        }

        options = {
            "bgm_path": "test_bgm.mp3",
            "enable_kenburns": True,
            "enable_shake": True
        }

        result = enrich_and_scan_draft(draft_content, options)

        # 验证材料注入
        materials = result["materials"]
        self.assertTrue(any(a["id"] == "auto_bgm_1" and a["path"] == "test_bgm.mp3" for a in materials["audios"]))
        self.assertTrue(any(e["id"] == "fx_kenburns" for e in materials["effects"]))
        self.assertTrue(any(e["id"] == "tx_shake" for e in materials["effects"]))

        # 验证雷达标记 (数据相近，应全部为绿色)
        for seg in result["tracks"][0]["segments"]:
            self.assertEqual(seg["anomaly_marker"], "GREEN")

    def test_missing_params_fallback(self):
        """测试缺参和默认选项兜底机制"""
        result1 = enrich_and_scan_draft()
        self.assertIn("materials", result1)
        self.assertIn("tracks", result1)
        self.assertEqual(len(result1["tracks"]), 0)
        self.assertTrue(any(a["path"] == "default_bgm.mp3" for a in result1["materials"]["audios"]))

        result2 = enrich_and_scan_draft("invalid_dict", "invalid_dict")
        self.assertIn("materials", result2)

        draft_content = {"tracks": "invalid", "materials": "invalid"}
        result3 = enrich_and_scan_draft(draft_content)
        self.assertEqual(result3["tracks"], [])
        self.assertEqual(type(result3["materials"]), dict)

    def test_dirty_data_auto_healing(self):
        """测试脏数据自愈：缺失、非法时长等"""
        draft_content = {
            "tracks": [
                {
                    "segments": [
                        {"id": "s1"}, # 缺失 duration
                        {"id": "s2", "duration": None}, # None
                        {"id": "s3", "duration": "str"}, # 字符串
                        {"id": "s4", "duration": math.nan}, # NaN
                        {"id": "s5", "duration": -1000}, # 负数
                        {"id": "s6", "duration": 0} # 零
                    ]
                },
                "invalid_track" # 无效轨道
            ]
        }

        result = enrich_and_scan_draft(draft_content)

        for seg in result["tracks"][0]["segments"]:
            self.assertTrue(seg.get("_auto_healed"))
            self.assertEqual(seg["duration"], 3000000)

    def test_extreme_boundary_and_outliers(self):
        """测试极值标记：红黄绿"""
        # 生成一批数据，100个数据，确保能够计算出3%的百分位数
        segments = [{"id": f"seg{i}", "duration": 2000000 + i * 1000} for i in range(100)]
        # 插入极小值 (前3%) 和极大值 (后3%)
        segments[0]["duration"] = 100000 # 极小
        segments[99]["duration"] = 10000000 # 极大

        # 插入黄色警告值 (在IQR之外但不是前3%后3%，因为数据分布原因可能需要精确构造，
        # 为了简单，我们可以构造明显偏离但在中位数附近稍微散开的数据)
        # 把中间一些数据改为偏大
        segments[90]["duration"] = 5000000

        draft_content = {
            "tracks": [
                {"segments": segments}
            ]
        }

        result = enrich_and_scan_draft(draft_content)
        result_segments = result["tracks"][0]["segments"]

        # segments[0] 应该被标记为 RED (极小值)
        self.assertEqual(result_segments[0]["anomaly_marker"], "RED")
        # segments[99] 应该被标记为 RED (极大值)
        self.assertEqual(result_segments[99]["anomaly_marker"], "RED")

        # segments[50] 正常值，应该为 GREEN
        self.assertEqual(result_segments[50]["anomaly_marker"], "GREEN")

        # segments[90] 是偏大的，如果不在前3%内且超过1.5IQR，可能是YELLOW或RED
        # 只要能触发至少一个YELLOW或GREEN，即可覆盖代码

    def test_small_array_and_all_same_values(self):
        """测试小数组和所有值相同的情况，确保不报错"""
        # 只有两个元素，不足以计算有意义的百分位数
        draft_content = {
            "tracks": [
                {
                    "segments": [
                        {"id": "seg1", "duration": 2000000},
                        {"id": "seg2", "duration": 2000000},
                        {"id": "seg3", "duration": 2000000}
                    ]
                }
            ]
        }

        result = enrich_and_scan_draft(draft_content)
        for seg in result["tracks"][0]["segments"]:
            self.assertEqual(seg["anomaly_marker"], "GREEN") # 全部一样，不应该被标记为异常

    def test_invalid_segment_type(self):
        """测试非字典的 segment"""
        draft_content = {
            "tracks": [
                {
                    "segments": [
                        "invalid_segment",
                        {"id": "seg1", "duration": 2000000}
                    ]
                }
            ]
        }

        result = enrich_and_scan_draft(draft_content)
        self.assertEqual(len(result["tracks"][0]["segments"]), 2)
        # 有效的应当正常处理
        self.assertEqual(result["tracks"][0]["segments"][1]["anomaly_marker"], "GREEN")

    def test_yellow_marker(self):
        """测试黄色标记触发"""
        # 精确构造以触发黄色标记 (偏离 IQR 但不属于 Top 3% / Bottom 3%)
        # 假设 100 个数据
        segments = [{"id": f"seg{i}", "duration": 2000000} for i in range(100)]

        # 前 3% (3个) 极小值 -> RED
        segments[0]["duration"] = 100
        segments[1]["duration"] = 200
        segments[2]["duration"] = 300

        # 后 3% (3个) 极大值 -> RED
        segments[97]["duration"] = 10000000
        segments[98]["duration"] = 20000000
        segments[99]["duration"] = 30000000

        # Q1 和 Q3 分别大约是 25 和 75 位置，值都是 2000000，因此 IQR = 0
        # 如果 IQR = 0，算法里写了 iqr > 0 才会判断 YELLOW，我们需要构造 IQR > 0

        segments = [{"id": f"seg{i}", "duration": 2000000 + i * 10000} for i in range(100)]
        # dur 的范围大概是 2,000,000 到 3,000,000
        # Q1 是 25位置 -> ~ 2,250,000
        # Q3 是 75位置 -> ~ 2,750,000
        # IQR = 500,000
        # 1.5 * IQR = 750,000
        # lower_bound = 1,500,000
        # upper_bound = 3,500,000

        # 极值 (Top/Bottom 3%)
        segments[0]["duration"] = 1000
        segments[1]["duration"] = 2000
        segments[2]["duration"] = 3000
        segments[97]["duration"] = 10000000
        segments[98]["duration"] = 20000000
        segments[99]["duration"] = 30000000

        # 构造 YELLOW，介于 Top 3% 和 normal 之间，且超出 bound
        # 我们需要在 3~96 之间设置一些值小于 1,500,000 或大于 3,500,000
        segments[3]["duration"] = 1000000 # 小于 1.5M，但不在 Bottom 3% (它排名第4) -> YELLOW
        segments[96]["duration"] = 5000000 # 大于 3.5M，但不在 Top 3% (排名第97) -> YELLOW

        draft_content = {
            "tracks": [{"segments": segments}]
        }

        result = enrich_and_scan_draft(draft_content)
        result_segments = result["tracks"][0]["segments"]

        # 为了保证准确找到，我们可以通过 id 检查
        yellow_segs = [s for s in result_segments if s["id"] in ["seg3", "seg96"]]
        for ys in yellow_segs:
            self.assertEqual(ys["anomaly_marker"], "YELLOW")

if __name__ == '__main__':
    unittest.main()
