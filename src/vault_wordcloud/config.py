"""Run configuration: which notes to read, where to write, and how the cloud looks.

Global context: every knob lives in Wordcloud/.env (template: .env.example) and is loaded with
python-dotenv (https://github.com/theskumar/python-dotenv#getting-started). A missing key falls back to the
defaults below, so the generator works with no .env at all. Relative paths resolve against the
Wordcloud/ project folder, not the shell's cwd, so `uv run vault-wordcloud` behaves the same from anywhere.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

import stopwordsiso
from dotenv import load_dotenv

# src/vault_wordcloud/config.py -> parents[2] is the Wordcloud/ project folder (pathlib: https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.parents).
PROJECT_DIR = Path(__file__).resolve().parents[2]


@dataclass
class Config:
    """All settings for one run; built by load_config() or directly in tests."""

    vault_dir: Path  # Obsidian vault root that the source paths are relative to
    source_files: list[str]  # individual notes, e.g. Home.md
    source_dirs: list[str]  # folders whose top-level *.md notes are all included, e.g. Articles
    output: Path  # PNG to write
    log_dir: Path  # where timestamped run logs go
    width: int  # canvas size in pixels
    height: int
    max_words: int  # cap on words drawn (WordCloud max_words)
    max_font_size: int  # pixel size of the most frequent word; the rest scale down from it
    relative_scaling: float  # 0..1, roughly the exponent in size ~ freq**rs; lower = big words relatively smaller
    random_state: int  # fixed seed -> identical layout and colours on every run
    # Added on top of wordcloud.STOPWORDS: stopwords.txt + stopwords-iso lists. repr=False keeps ~450 words out of the
    # logged config (dataclass field options: https://docs.python.org/3/library/dataclasses.html#dataclasses.field).
    extra_stopwords: set[str] = field(repr=False)


def _csv(name: str, default: str) -> list[str]:
    """Read a comma-separated env var into a list of trimmed, non-empty items."""
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def _wordlist(path: Path) -> set[str]:
    """Read one lowercase word per line, ignoring blank lines and '#' comments."""
    lines = (line.split("#", 1)[0].strip().lower() for line in path.read_text(encoding="utf-8").splitlines())
    return {line for line in lines if line}


def load_config() -> Config:
    """Load Wordcloud/.env (if present) into os.environ and build a Config from it."""
    load_dotenv(PROJECT_DIR / ".env")  # does not override variables already set in the shell
    return Config(
        vault_dir=(PROJECT_DIR / os.getenv("VAULT_DIR", "..")).resolve(),
        source_files=_csv("SOURCE_FILES", "Home.md,Exocortex.md,About me and my experience.md"),
        source_dirs=_csv("SOURCE_DIRS", "Articles"),
        output=PROJECT_DIR / os.getenv("OUTPUT", "wordcloud.png"),
        log_dir=PROJECT_DIR / os.getenv("LOG_DIR", "logs"),
        width=int(os.getenv("WIDTH", "2000")),
        height=int(os.getenv("HEIGHT", "1200")),
        max_words=int(os.getenv("MAX_WORDS", "200")),
        max_font_size=int(os.getenv("MAX_FONT_SIZE", "300")),
        relative_scaling=float(os.getenv("RELATIVE_SCALING", "0.4")),
        random_state=int(os.getenv("RANDOM_STATE", "42")),
        # Some Articles are partly Czech, so Czech function words (je, ale, co...) are filtered via stopwords-iso
        # (https://github.com/stopwords-iso/stopwords-cs, Python wrapper https://github.com/bact/stopwords-iso).
        extra_stopwords=_wordlist(PROJECT_DIR / os.getenv("STOPWORDS_FILE", "stopwords.txt"))
        | stopwordsiso.stopwords(_csv("STOPWORD_LANGS", "cs")),
    )
