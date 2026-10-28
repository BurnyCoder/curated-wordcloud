"""Phase 1: find the notes to include and read them.

Global context: the cloud is built from a fixed set of vault notes (Home, Exocortex, About me)
plus every note directly inside the listed folders (Articles). A listed note that is missing raises an
error instead of being skipped quietly, so a renamed note can't silently drop out of the cloud.
"""

import logging
from pathlib import Path

log = logging.getLogger(__name__)


def collect_sources(vault_dir: Path, source_files: list[str], source_dirs: list[str]) -> list[Path]:
    """Return the listed notes followed by each folder's top-level *.md notes, sorted for a stable order."""
    paths = [vault_dir / name for name in source_files]
    missing = [str(p) for p in paths if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"Listed source notes not found: {missing}")
    for folder in source_dirs:
        # Path.glob("*.md") is non-recursive, so subfolders (e.g. drafts) are not pulled in (https://docs.python.org/3/library/pathlib.html#pathlib.Path.glob).
        paths += sorted((vault_dir / folder).glob("*.md"))
    return paths


def read_notes(paths: list[Path], vault_dir: Path) -> list[str]:
    """Read each note as UTF-8 and log its size, so the run log shows exactly what went in."""
    texts = []
    for path in paths:
        texts.append(path.read_text(encoding="utf-8"))
        log.info("Read %6d chars  %s", len(texts[-1]), path.relative_to(vault_dir))
    return texts
