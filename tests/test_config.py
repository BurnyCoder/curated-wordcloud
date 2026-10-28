"""Tests for load_config: defaults point at the real vault notes and the stopword sources are merged.

Global context: these read the real Wordcloud/stopwords.txt and the stopwords-iso Czech list, so they
catch a broken path or a dropped language before a run produces a cloud full of "je"/"ale" or "Wikipedia".
"""

import pytest

from vault_wordcloud.config import load_config


def test_default_sources_exist_in_vault():
    config = load_config()
    # A standalone clone of the public mirror has no vault next to it; Obsidian marks a vault root with .obsidian/.
    if not (config.vault_dir / ".obsidian").is_dir():
        pytest.skip(f"no Obsidian vault at {config.vault_dir} (standalone clone)")  # https://docs.pytest.org/en/stable/how-to/skipping.html
    assert all((config.vault_dir / name).is_file() for name in config.source_files)
    assert all((config.vault_dir / folder).is_dir() for folder in config.source_dirs)


def test_stopwords_merge_file_and_czech_list():
    words = load_config().extra_stopwords
    assert {"wikipedia", "etc"} <= words  # from stopwords.txt
    assert {"je", "ale"} <= words  # from stopwordsiso.stopwords("cs")
    assert "#" not in "".join(words)  # comments are stripped
