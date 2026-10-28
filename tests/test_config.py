"""Tests for load_config: defaults point at the real vault notes and stopwords.txt is parsed.

Global context: these read the real Wordcloud/stopwords.txt, so they catch a broken path or comment
handling before a run produces a cloud full of filler like "Wikipedia" or "etc".
"""

from vault_wordcloud.config import load_config


def test_default_sources_exist_in_vault():
    config = load_config()
    assert all((config.vault_dir / name).is_file() for name in config.source_files)
    assert all((config.vault_dir / folder).is_dir() for folder in config.source_dirs)


def test_stopwords_file_is_loaded_without_comments():
    words = load_config().extra_stopwords
    assert {"wikipedia", "etc"} <= words
    assert "#" not in "".join(words)  # comments are stripped
