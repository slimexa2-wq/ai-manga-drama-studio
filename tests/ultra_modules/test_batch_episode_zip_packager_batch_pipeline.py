import unittest
import asyncio
import os
import shutil
import tempfile
import zipfile

from ultra_modules.batch_episode_zip_packager_batch_pipeline import BatchEpisodeZipPackagerPipeline, ProgressSnapshot

class TestBatchEpisodeZipPackagerPipeline(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.pipeline = BatchEpisodeZipPackagerPipeline(max_workers=5)
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        self.pipeline.shutdown()
        shutil.rmtree(self.test_dir)

    async def test_normal_behavior(self):
        """Test #1: Normal behavior with valid inputs"""
        # Create dummy mp4 and srt files
        mp4_path = os.path.join(self.test_dir, 'test.mp4')
        with open(mp4_path, 'wb') as f:
            f.write(b"real video content")

        srt_path = os.path.join(self.test_dir, 'test.srt')
        with open(srt_path, 'w') as f:
            f.write("real subtitle")

        records = [{
            'episode_id': 'ep1',
            'mp4_path': mp4_path,
            'srt_path': srt_path,
            'draft_data': '{"foo": "bar"}',
            'prompt_data': 'test prompt'
        }]

        output_dir = os.path.join(self.test_dir, 'output')

        snapshots = []
        async for snapshot in self.pipeline.process_batch_stream(records, output_dir):
            snapshots.append(snapshot)

        self.assertTrue(len(snapshots) > 0)
        final_snapshot = snapshots[-1]
        self.assertTrue(final_snapshot.is_done)
        self.assertEqual(final_snapshot.total, 1)
        self.assertEqual(final_snapshot.completed, 1)
        self.assertEqual(final_snapshot.failed, 0)

        # Verify the ZIP file
        result = final_snapshot.results[0]
        self.assertEqual(result['status'], 'success')
        zip_path = result['zip_path']
        self.assertTrue(os.path.exists(zip_path))

        with zipfile.ZipFile(zip_path, 'r') as zf:
            files = zf.namelist()
            self.assertIn('ep1.mp4', files)
            self.assertIn('ep1.srt', files)
            self.assertIn('ep1_draft.json', files)
            self.assertIn('ep1_prompt.txt', files)

    async def test_dirty_data_auto_healing(self):
        """Test #2: Dirty data auto-healing (e.g. non-dict records)"""
        # Pass a string instead of a dict
        records = ["this is just a string, not a valid record dict"]
        output_dir = os.path.join(self.test_dir, 'output')

        snapshots = []
        async for snapshot in self.pipeline.process_batch_stream(records, output_dir):
            snapshots.append(snapshot)

        final_snapshot = snapshots[-1]
        self.assertTrue(final_snapshot.is_done)
        self.assertEqual(final_snapshot.completed, 1)

        result = final_snapshot.results[0]
        self.assertEqual(result['status'], 'success')

        # Check fallback files in zip
        with zipfile.ZipFile(result['zip_path'], 'r') as zf:
            files = zf.namelist()
            # Episode ID will be a generated UUID, so we can't check exact names, but we can check suffixes
            self.assertTrue(any(f.endswith('_fallback.mp4') for f in files))
            self.assertTrue(any(f.endswith('_fallback.srt') for f in files))

    async def test_missing_parameters_fallback(self):
        """Test #3: Missing parameters fallback (empty dict)"""
        records = [{}]
        output_dir = os.path.join(self.test_dir, 'output2')

        snapshots = []
        async for snapshot in self.pipeline.process_batch_stream(records, output_dir):
            snapshots.append(snapshot)

        final_snapshot = snapshots[-1]
        self.assertTrue(final_snapshot.is_done)
        self.assertEqual(final_snapshot.completed, 1)

        result = final_snapshot.results[0]
        self.assertEqual(result['status'], 'success')

        with zipfile.ZipFile(result['zip_path'], 'r') as zf:
            files = zf.namelist()
            # Should have fallback content
            draft_file = next(f for f in files if f.endswith('_draft.json'))
            prompt_file = next(f for f in files if f.endswith('_prompt.txt'))

            self.assertEqual(zf.read(draft_file).decode('utf-8'), '{"version": "1.0", "type": "draft"}')
            self.assertEqual(zf.read(prompt_file).decode('utf-8'), 'Default Manga Prompt')

    async def test_extreme_boundaries(self):
        """Test #4: Extreme boundaries (processing 1000 records)"""
        records = [{'episode_id': f'batch_{i}'} for i in range(1000)]
        output_dir = os.path.join(self.test_dir, 'output_large')

        snapshots = []
        async for snapshot in self.pipeline.process_batch_stream(records, output_dir):
            snapshots.append(snapshot)

        final_snapshot = snapshots[-1]
        self.assertTrue(final_snapshot.is_done)
        self.assertEqual(final_snapshot.total, 1000)
        self.assertEqual(final_snapshot.completed, 1000)
        self.assertEqual(final_snapshot.failed, 0)
        self.assertEqual(len(final_snapshot.results), 1000)

    async def test_async_progress_snapshots(self):
        """Test #5: Async progress snapshots behavior (non-blocking yield)"""
        records = [{'episode_id': f'snaps_{i}'} for i in range(10)]
        output_dir = os.path.join(self.test_dir, 'output_snaps')

        snapshots = []
        async for snapshot in self.pipeline.process_batch_stream(records, output_dir):
            snapshots.append(snapshot)

        # Should yield at least start snapshot + 10 completion snapshots
        self.assertTrue(len(snapshots) > 1)

        # Verify first snapshot
        first_snapshot = snapshots[0]
        self.assertEqual(first_snapshot.total, 10)
        self.assertEqual(first_snapshot.completed, 0)
        self.assertEqual(first_snapshot.in_progress, 10)
        self.assertFalse(first_snapshot.is_done)

        # Verify monotonically increasing completions
        completions = [s.completed for s in snapshots]
        self.assertEqual(completions, sorted(completions))

        # Verify last snapshot
        last_snapshot = snapshots[-1]
        self.assertTrue(last_snapshot.is_done)
        self.assertEqual(last_snapshot.in_progress, 0)
        self.assertEqual(last_snapshot.completed, 10)

if __name__ == '__main__':
    unittest.main()
