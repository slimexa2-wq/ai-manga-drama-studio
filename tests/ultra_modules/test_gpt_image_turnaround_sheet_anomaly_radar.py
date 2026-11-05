import unittest
from ultra_modules.gpt_image_turnaround_sheet_anomaly_radar import scan_turnaround_sheet_anomalies

class TestGPTImageTurnaroundSheetAnomalyRadar(unittest.TestCase):

    def test_normal_data(self):
        """测试正常数据（大部分数据均分布在均值附近，绿灯放行）"""
        # 生成 20 个接近的正常数据
        data = [{'id': f'item_{i}', 'complexity_score': 10 + (i * 0.1)} for i in range(20)]
        result = scan_turnaround_sheet_anomalies(data)

        for item in result:
            self.assertEqual(item['anomaly_color'], 'Green')
            self.assertIn('静默放行', item['anomaly_reason'])

    def test_extreme_boundary_red_flag(self):
        """测试极度异常数据（Top 3%边界，红灯拦截）"""
        # 生成 100 个数据，99 个在 10 左右，1 个在 1000（极端异常）
        data = [{'id': f'item_{i}', 'complexity_score': 10.0} for i in range(99)]
        data.append({'id': 'anomaly_item', 'complexity_score': 1000.0})

        result = scan_turnaround_sheet_anomalies(data)

        # 寻找极端异常的项
        anomaly = next(item for item in result if item['id'] == 'anomaly_item')
        self.assertEqual(anomaly['anomaly_color'], 'Red')
        self.assertIn('前3%极度异常', anomaly['anomaly_reason'])

        # 其他项应该是绿灯
        normal_items = [item for item in result if item['id'] != 'anomaly_item']
        for item in normal_items:
            self.assertEqual(item['anomaly_color'], 'Green')

    def test_yellow_flag_data(self):
        """测试边缘异常数据（Top 10%边界，黄灯警告）"""
        # 构造数据使一个点 Z-score 恰好在 1.64 到 2.17 之间，或者 IQR 在 1.5 到 2.5 之间。
        # 比如10个正常，1个偏离不至于极大。
        data = [{'id': f'item_{i}', 'complexity_score': 10.0} for i in range(10)]
        # 添加一些微小波动确保标准差不为0
        data[0]['complexity_score'] = 9.9
        data[1]['complexity_score'] = 10.1
        data.append({'id': 'yellow_item', 'complexity_score': 10.0 + 2.0 * 0.1}) # 手动试探，更好的做法是给出相对偏离

        # 换种方式明确控制，100个数据，
        # mean=10, std约1，正常分布
        # 让一个数据距离均值约 1.8 个 std
        data = []
        for i in range(99):
            if i % 2 == 0:
                data.append({'id': f'item_{i}', 'complexity_score': 9.0})
            else:
                data.append({'id': f'item_{i}', 'complexity_score': 11.0})
        # 此时 mean=10, std=1左右
        # 添加一个值为 11.8 的，Z-score 约 1.8，落在黄区(>1.64 且 <2.17)
        data.append({'id': 'yellow_item', 'complexity_score': 11.8})

        result = scan_turnaround_sheet_anomalies(data)
        yellow_item = next(item for item in result if item['id'] == 'yellow_item')
        self.assertEqual(yellow_item['anomaly_color'], 'Yellow')
        self.assertIn('边缘10%', yellow_item['anomaly_reason'])

    def test_dirty_data_self_healing(self):
        """测试脏数据自愈（非字典数据自动包装，不可转数值的数据自动置0）"""
        data = [
            "I am a dirty string",
            123,
            {'id': 'item_3', 'complexity_score': 'not_a_number'},
            {'id': 'item_4', 'complexity_score': '15.5'} # 可转数值的字符串
        ]
        result = scan_turnaround_sheet_anomalies(data)

        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]['complexity_score'], 0.0) # 字符串脏数据
        self.assertEqual(result[1]['complexity_score'], 0.0) # 数字脏数据
        self.assertEqual(result[2]['complexity_score'], 0.0) # 字典内字符串不可转数值
        self.assertEqual(result[3]['complexity_score'], 15.5) # 字典内字符串可转数值

    def test_missing_params_fallback(self):
        """测试缺参默认兜底（None, 空列表, 极少数据）"""
        # 测试 None
        result_none = scan_turnaround_sheet_anomalies(None)
        self.assertEqual(result_none, [])

        # 测试空列表
        result_empty = scan_turnaround_sheet_anomalies([])
        self.assertEqual(result_empty, [])

        # 测试极少数据（不足3条，默认绿灯）
        result_few = scan_turnaround_sheet_anomalies([{'val': 100}, {'val': 1000}], metrics_key='val')
        self.assertEqual(len(result_few), 2)
        self.assertEqual(result_few[0]['anomaly_color'], 'Green')
        self.assertEqual(result_few[1]['anomaly_color'], 'Green')
        self.assertIn('数据量过少', result_few[0]['anomaly_reason'])

if __name__ == '__main__':
    unittest.main()
