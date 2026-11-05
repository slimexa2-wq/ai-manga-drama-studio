import time
import copy

class CharacterDnaSeedLockerSelfHealingGuard:
    """
    全剧角色视觉DNA跨100集硬锁定器。
    具备异常输入静默自愈与5秒一键撤回(Undo)快照机制。
    极简设计：不抛出任何异常，静默处理所有脏数据。
    """
    def __init__(self):
        self.dna_store = {}
        self.snapshots = {}
        self.default_dna = {
            'hair_color': 'black',
            'eye_color': 'black',
            'clothing': 'casual',
            'style_suffix': 'anime',
            'seed': 42
        }

    def _heal_character_name(self, character_name):
        if character_name is None:
            return 'UnknownCharacter'
        if not isinstance(character_name, str):
            character_name = str(character_name)
        character_name = character_name.strip()
        if not character_name:
            return 'UnknownCharacter'
        return character_name

    def _heal_dna_data(self, dna_data):
        if not isinstance(dna_data, dict):
            dna_data = {}

        healed_data = {}
        for key, default_val in self.default_dna.items():
            val = dna_data.get(key)
            if val is None:
                healed_data[key] = default_val
            elif isinstance(val, str) and not val.strip():
                healed_data[key] = default_val
            elif key == 'seed':
                try:
                    healed_data[key] = int(val)
                except (ValueError, TypeError):
                    healed_data[key] = default_val
            else:
                healed_data[key] = str(val).strip()

        return healed_data

    def lock_dna(self, character_name, dna_data):
        name = self._heal_character_name(character_name)
        data = self._heal_dna_data(dna_data)

        if name not in self.snapshots:
            self.snapshots[name] = []

        current_time = time.time()

        if name in self.dna_store:
            self.snapshots[name].append((current_time, copy.deepcopy(self.dna_store[name])))

        self.dna_store[name] = data
        return copy.deepcopy(data)

    def get_dna(self, character_name):
        name = self._heal_character_name(character_name)
        if name not in self.dna_store:
            return self._heal_dna_data({})
        return copy.deepcopy(self.dna_store[name])

    def undo(self, character_name):
        name = self._heal_character_name(character_name)
        if name not in self.snapshots or not self.snapshots[name]:
            return False

        current_time = time.time()

        while self.snapshots[name]:
            snapshot_time, snapshot_data = self.snapshots[name].pop()
            # 5秒内允许撤回，给予0.1秒容差
            if current_time - snapshot_time <= 5.1:
                self.dna_store[name] = snapshot_data
                return True
            else:
                # 超过5秒的快照已失效，不可撤回
                continue

        return False
