import unittest
import time
from ultra_modules.ego_dual_cloud_dispatcher_self_healing_guard import EgoDualCloudDispatcher

class TestEgoDualCloudDispatcherSelfHealingGuard(unittest.TestCase):
    def setUp(self):
        self.dispatcher = EgoDualCloudDispatcher(undo_window_seconds=1)

    def test_normal_execution(self):
        """Test normal dispatching with valid data."""
        data = {
            'model': 'gpt-4o',
            'provider': 'openai',
            'parameters': {
                'max_tokens': 1000,
                'temperature': 0.5
            }
        }
        task_id, result = self.dispatcher.dispatch_task(data)

        self.assertIsNotNone(task_id)
        self.assertEqual(result['model'], 'gpt-4o')
        self.assertEqual(result['provider'], 'openai')
        self.assertEqual(result['parameters']['max_tokens'], 1000)
        self.assertEqual(result['parameters']['temperature'], 0.5)
        self.assertIn(task_id, self.dispatcher.dispatched_tasks)

    def test_missing_parameter_fallbacks(self):
        """Test fallback mechanisms for missing parameters."""
        data = {}
        task_id, result = self.dispatcher.dispatch_task(data)

        self.assertEqual(result['model'], 'gemini-3.1-pro')
        self.assertEqual(result['provider'], 'google')
        self.assertEqual(result['parameters']['max_tokens'], 2048)
        self.assertEqual(result['parameters']['temperature'], 0.7)

        # Test inferring openai provider
        data2 = {'model': 'sora'}
        _, result2 = self.dispatcher.dispatch_task(data2)
        self.assertEqual(result2['provider'], 'openai')

    def test_dirty_data_healing(self):
        """Test healing of dirty data types (e.g. strings instead of numbers)."""
        data = {
            'parameters': {
                'max_tokens': "1500",
                'temperature': "0.9"
            }
        }
        task_id, result = self.dispatcher.dispatch_task(data)

        self.assertEqual(result['parameters']['max_tokens'], 1500)
        self.assertEqual(result['parameters']['temperature'], 0.9)
        self.assertIsInstance(result['parameters']['max_tokens'], int)
        self.assertIsInstance(result['parameters']['temperature'], float)

    def test_extreme_edge_cases(self):
        """Test handling of extremely malformed or None data."""
        # None as input
        task_id1, result1 = self.dispatcher.dispatch_task(None)
        self.assertEqual(result1['model'], 'gemini-3.1-pro')
        self.assertEqual(result1['parameters']['max_tokens'], 2048)

        # Completely invalid types
        data2 = {
            'parameters': {
                'max_tokens': [1, 2, 3],  # Invalid list
                'temperature': {'invalid': 'dict'} # Invalid dict
            }
        }
        task_id2, result2 = self.dispatcher.dispatch_task(data2)
        self.assertEqual(result2['parameters']['max_tokens'], 2048)
        self.assertEqual(result2['parameters']['temperature'], 0.7)

        # Temperature out of bounds
        data3 = {
            'parameters': {
                'temperature': 5.0
            }
        }
        _, result3 = self.dispatcher.dispatch_task(data3)
        self.assertEqual(result3['parameters']['temperature'], 1.0)

        data4 = {
            'parameters': {
                'temperature': -1.5
            }
        }
        _, result4 = self.dispatcher.dispatch_task(data4)
        self.assertEqual(result4['parameters']['temperature'], 0.0)

    def test_undo_mechanism(self):
        """Test the snapshot-based undo mechanism."""
        data = {'model': 'o3'}
        task_id, result = self.dispatcher.dispatch_task(data)

        # Verify it's dispatched
        self.assertIn(task_id, self.dispatcher.dispatched_tasks)

        # Undo immediately (within window)
        success, msg = self.dispatcher.undo_task(task_id)
        self.assertTrue(success)
        self.assertNotIn(task_id, self.dispatcher.dispatched_tasks)
        self.assertNotIn(task_id, self.dispatcher.snapshots)

        # Test expiration
        task_id2, _ = self.dispatcher.dispatch_task(data)
        time.sleep(1.1)  # Wait for undo window to expire

        success2, msg2 = self.dispatcher.undo_task(task_id2)
        self.assertFalse(success2)
        self.assertEqual(msg2, "Undo window expired.")
        self.assertIn(task_id2, self.dispatcher.dispatched_tasks)

if __name__ == '__main__':
    unittest.main()
