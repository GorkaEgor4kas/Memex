'''Indexing logic'''
import json
from pathlib import Path
from typing import Dict, Any, Set
from datetime import datetime

from memex.utils.file_utils import compute_file_hash, get_relative_path


class IndexState:
    '''Manage the index state json files'''

    def __init__(self):
        self.state_path = Path.home() / ".obsidian-rag" / "index_state.json"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        '''Load index state from disk'''
        if not self.state_path.exists():
            return self._empty_state()
        
        with open(self.state_path, 'r', encoding='utf-8') as f:
            return json.load(f)
        

    def save(self, files: Set[Path], vault_path: Path) -> None:
        '''Save current index state to disk'''
        state = {
            "version": '1.0',
            "last_full_index": datetime.now().isoformat(),
            "vault_path": str(vault_path),
            "files": {}
        }

        for file_path in files:
            relative_path = get_relative_path(file_path, vault_path)
            state["files"][relative_path] ={
                "hash": compute_file_hash(file_path),
                "modified": file_path.stat().st_mtime,
                "indexed_at": datetime.now().isoformat(),
            }

        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)  

    def get_file_hash(self, file_path: str) -> str | None:
        '''Get stored hash for a file from the state.'''
        state = self.load()
        files = state.get("files")
        if file_path in files:
            return files[file_path].get("hash")  
        return None
        
    def is_file_changed(self, file_path: Path, vault_path: Path) -> bool:
        '''Check if the file has changed since the last indexing'''
        relative_path = get_relative_path(file_path, vault_path)
        stored_hash = self.get_file_hash(relative_path) 

        #file is new
        if stored_hash is None:
            return True

        current_hash = compute_file_hash(file_path)
        return current_hash != stored_hash

    def update_chunks_count(self, file_path: Path, vault_path: Path, count: int) -> None:
        '''Function to update chunks size for each file. Will be called during chunking, I guess'''
        state = self.load()
        files = state.get("files", {})
        relative_path = get_relative_path(file_path, vault_path)
        if relative_path in files:
            files[relative_path]['chunks_count'] = count
            with open(self.state_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

    def remove_file(self, file_path: Path, vault_path: Path) -> None:
        '''Remove a file from the index state (call when deleted from the vault)'''
        state = self.load()
        files = state.get('files', {})
        relative_path = get_relative_path(file_path, vault_path)
        if relative_path in files:
            del files[relative_path]
            with open(self.state_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        pass

    def _empty_state(self) -> Dict[str, Any]:
        '''Return an emtpy state structure'''
        return {
            "version": "1.0",
            "last_full_index": None,
            "vault_path": None,
            "files": {}
        }
    