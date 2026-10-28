"""Entry point: build the vault word cloud by running the phases in order.

Global context: `uv run vault-wordcloud` calls main() (wired in pyproject.toml [project.scripts],
https://docs.astral.sh/uv/concepts/projects/config/#entry-points). The phases are:
  1. sources.collect_sources / read_notes  - pick and read the notes
  2. clean.clean_markdown                  - strip Obsidian markup down to prose
  3. render.render_wordcloud               - count words and save the PNG
"""

import logging

from vault_wordcloud.clean import clean_markdown
from vault_wordcloud.config import Config, load_config
from vault_wordcloud.logs import setup_logging
from vault_wordcloud.render import render_wordcloud
from vault_wordcloud.sources import collect_sources, read_notes

log = logging.getLogger(__name__)


def run(config: Config) -> dict[str, int]:
    """Run all phases for one config and return the word counts the cloud was drawn from."""
    log_file = setup_logging(config.log_dir)
    log.info("Config: %s (+%d extra stopwords)", config, len(config.extra_stopwords))
    paths = collect_sources(config.vault_dir, config.source_files, config.source_dirs)
    log.info("Collected %d notes", len(paths))
    text = "\n\n".join(clean_markdown(note) for note in read_notes(paths, config.vault_dir))
    log.info("Cleaned text: %d chars", len(text))
    counts = render_wordcloud(text, config)
    top = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:30]
    log.info("Top 30 of %d distinct terms: %s", len(counts), ", ".join(f"{w} ({c})" for w, c in top))
    log.info("Saved %s  (log: %s)", config.output, log_file)
    return counts


def main() -> None:
    """CLI entry: load .env config and run; a crash is logged with its traceback so the run log explains it."""
    try:
        run(load_config())
    except Exception:
        log.exception("Run failed")  # logging.exception adds the traceback (https://docs.python.org/3/library/logging.html#logging.Logger.exception)
        raise


if __name__ == "__main__":
    main()
