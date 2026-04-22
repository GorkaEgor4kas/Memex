'''Tests for IndexState module'''
import pytest
import json
from pathlib import Path
from indexing.index_state import IndexState
from utils.file_utils import compute_file_hash

@pytest.fixture
def temp_vault(tmp_path):
    '''Creata a temporary vault with test cases'''
    vault = tmp_path / "vault"
    vault.mkdir()

    test_file = vault / "test.md"
    test_file.write_text("# Hello\n world!", encoding="utf-8")

    return vault

@pytest.fixture
def index_state(tmp_path, monkeypatch):
    '''Create IndexState with temporary path'''
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return IndexState()

def test_save_n_load(index_state, temp_vault):
    '''Test saving and loading state'''
    files = set(temp_vault.rglob("*.md"))

    #save
    index_state.save(files, temp_vault)

    #load
    state = index_state.load()
    
    assert state["version"] == "1.0"
    assert state["vault_path"] == str(temp_vault)
    assert "test.md" in state["files"]
    assert state["files"]["test.md"]["hash"] == compute_file_hash(temp_vault / "test.md")

def test_is_file_changed_new_file(index_state, temp_vault):
    """New file should be detected as changed."""
    test_file = temp_vault / "test.md"
    assert index_state.is_file_changed(test_file, temp_vault) is True

def test_is_file_changed_unchanged(index_state, temp_vault):
    """Unchanged file should not be detected as changed."""
    test_file = temp_vault / "test.md"
    
    # first time - new file
    index_state.save({test_file}, temp_vault)
    
    # second time — without changes
    assert index_state.is_file_changed(test_file, temp_vault) is False

def test_is_file_changed_modified(index_state, temp_vault):
    """Modified file should be detected as changed."""
    test_file = temp_vault / "test.md"
    
    # save initial state
    index_state.save({test_file}, temp_vault)
    
    # file changing
    test_file.write_text("# Modified content", encoding="utf-8")
    
    assert index_state.is_file_changed(test_file, temp_vault) is True

def test_update_chunks_count(index_state, temp_vault):
    """Test updating chunks count."""
    test_file = temp_vault / "test.md"
    
    # save file firstly
    index_state.save({test_file}, temp_vault)
    
    # updating chunks amount
    index_state.update_chunks_count(test_file, temp_vault, 5)
    
    # check
    state = index_state.load()
    assert state["files"]["test.md"]["chunks_count"] == 5

def test_remove_file(index_state, temp_vault):
    """Test removing file from state."""
    test_file = temp_vault / "test.md"
    
    # save
    index_state.save({test_file}, temp_vault)
    
    # delete
    index_state.remove_file(test_file, temp_vault)
    
    # check
    state = index_state.load()
    assert "test.md" not in state["files"]
