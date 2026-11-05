import os
import zipfile
import shutil
import time
import uuid

class BatchEpisodeZipPackagerSelfHealingGuard:
    def __init__(self, output_dir="output_zips"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir, exist_ok=True)
            except Exception:
                pass
        self.snapshots = {}

    def _heal_episode_data(self, data, index):
        """
        Silently heal data and provide defaults.
        Handles missing parameters and dirty data (e.g. None, invalid types).
        """
        if not isinstance(data, dict):
            data = {}

        # Ensure episode number is an integer
        try:
            ep_num = int(data.get('episode_number', index + 1))
        except (ValueError, TypeError):
            ep_num = index + 1

        healed_data = {
            'episode_number': ep_num,
            'mp4_path': str(data.get('mp4_path', '')) if data.get('mp4_path') else f'default_video_ep{ep_num}.mp4',
            'srt_path': str(data.get('srt_path', '')) if data.get('srt_path') else f'default_subtitles_ep{ep_num}.srt',
            'draft_content': str(data.get('draft_content', '')) if data.get('draft_content') else '{"default": "draft"}',
            'prompts': str(data.get('prompts', '')) if data.get('prompts') else 'default dual-eco prompts',
        }
        return healed_data

    def package_episodes(self, episodes_data, output_filename=None):
        """
        Packages multiple episodes into a single ZIP file.
        Returns the path to the ZIP file and a snapshot ID for undoing.
        """
        if not isinstance(episodes_data, list):
            episodes_data = [episodes_data]

        healed_episodes = [self._heal_episode_data(ep, i) for i, ep in enumerate(episodes_data)]

        if not isinstance(output_filename, str) or not output_filename.strip():
            output_filename = f"batch_episodes_{uuid.uuid4().hex[:8]}.zip"

        if not output_filename.endswith(".zip"):
            output_filename += ".zip"

        zip_path = os.path.join(self.output_dir, output_filename)

        # Create a snapshot for undo
        snapshot_id = str(uuid.uuid4())
        backup_path = f"{zip_path}.backup_{snapshot_id}"

        if os.path.exists(zip_path):
            try:
                shutil.copy2(zip_path, backup_path)
            except Exception:
                backup_path = None
            self.snapshots[snapshot_id] = {
                'action': 'overwrite',
                'zip_path': zip_path,
                'backup_path': backup_path,
                'timestamp': time.time()
            }
        else:
            self.snapshots[snapshot_id] = {
                'action': 'create',
                'zip_path': zip_path,
                'backup_path': None,
                'timestamp': time.time()
            }

        # Perform ZIP packaging
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for ep in healed_episodes:
                    ep_num = ep['episode_number']

                    def write_file_to_zip(arcname, path_or_content):
                        try:
                            if os.path.isfile(path_or_content):
                                zf.write(path_or_content, arcname)
                            else:
                                zf.writestr(arcname, path_or_content)
                        except Exception:
                            # Self-healing: if writing fails, write dummy content
                            zf.writestr(arcname, "error_fallback_content")

                    write_file_to_zip(f'episode_{ep_num}/video.mp4', ep['mp4_path'])
                    write_file_to_zip(f'episode_{ep_num}/subtitles.srt', ep['srt_path'])
                    write_file_to_zip(f'episode_{ep_num}/jianying_draft.json', ep['draft_content'])
                    write_file_to_zip(f'episode_{ep_num}/prompts.txt', ep['prompts'])
        except Exception:
            # Self-healing: if anything catastrophically fails during zip creation, try to make a fallback zip
            try:
                with zipfile.ZipFile(zip_path, 'w') as zf:
                    zf.writestr('error.log', 'Failed to generate package, fallback activated.')
            except Exception:
                pass

        return zip_path, snapshot_id

    def undo(self, snapshot_id):
        """
        Reverts the packaging action based on the snapshot ID.
        Enforces a 5-second one-click undo mechanism.
        """
        if not isinstance(snapshot_id, str) or snapshot_id not in self.snapshots:
            return False

        snapshot = self.snapshots[snapshot_id]

        # Enforce 5-second undo limit
        if time.time() - snapshot['timestamp'] > 5.0:
            return False

        zip_path = snapshot['zip_path']

        try:
            if snapshot['action'] == 'create':
                if os.path.exists(zip_path):
                    os.remove(zip_path)
            elif snapshot['action'] == 'overwrite':
                backup_path = snapshot['backup_path']
                if backup_path and os.path.exists(backup_path):
                    shutil.copy2(backup_path, zip_path)
                    os.remove(backup_path)
        except Exception:
            return False

        del self.snapshots[snapshot_id]
        return True
