import pytest
from pathlib import Path
from utils.file_utils import get_relative_path


def test_get_relative_path():
    vault = Path("/home/user/Obsidian")
    file_path = vault / "Projects" / "Alpha.md"
    
    result = Path(get_relative_path(file_path, vault))
    
    assert result == Path("Projects/Alpha.md")