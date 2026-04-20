'''
for hashes
'''

import json
from pathlib import Path
from typing import Dict, Any, Set
from datetime import datetime

from utils.file_utils import compute_file_hash, get_relative_path


class IndexState:
    '''Manage the index state json files'''

    def __init__(self):
        self.state_path = Path.home() / ".obsidian-rag" / "index_state.json"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        if not self.state_path.exists():
            return self._empty_state()
        
        with open(self.state_path, 'r', encoding='utf-8') as f:
            return json.load(f)
        

    def save(self, files: Set[Path], vault_path: Path) -> None:
        '''Save current index state to disk'''
        state = {
            "version": '1.0',
            "last_full_index": datetime.isoformat(),
            "vault_path": vault_path,
            "files": {}
        }

        for file_path in files:
            relative_path = get_relative_path(file_path, vault_path)
            state["files"][relative_path] ={
                "hash": compute_file_hash,
                "modified": file_path.stat().st_mtime,
                "indexed_at": datetime.now().isoformat(),
            }

        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(state, indent=2, ensure_ascii=False)  

    def get_file_hash():
        pass
        #STOPED HERE

    def _empty_state(self):
        pass




