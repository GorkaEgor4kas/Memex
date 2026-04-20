from pathlib import Path
from typing import Set
import hashlib

def get_all_md_files(vault_path: Path) -> Set[Path]:
    """Recursively find all .md files in vault, excluding .obsidian folder."""
    if not vault_path.exists():
        raise FileNotFoundError(f"Vault path does not exist: {vault_path}")
    
    md_files = set()

    for file_path in vault_path.rglob("*.md"):
        # Skip files inside hidden folders (like .obsidian, .git, .trash)
        if any(part.startswith(".") for part in file_path.parts):
            continue

        md_files.add(file_path)

    return md_files


def compute_file_hash(file_path: Path) -> str:
    '''Compute file SHA-256 hash'''
    hasher = hashlib.sha256()

    with open(file_path, 'rb') as f:
        #reading using chunks 
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    
    return hasher.hexdigest()

def get_relative_path(file_path: Path, vault_path: Path) -> str:
    """Get file path relative to vault root."""
    return str(file_path.relative_to(vault_path))


def ensure_dir(path: Path) -> None:
    """Create directory and all parents if they don't exist."""
    path.mkdir(parents=True, exist_ok=True)


