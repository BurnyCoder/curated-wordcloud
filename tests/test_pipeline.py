"""End-to-end smoke test: a tiny fake vault goes through every phase and yields a PNG.

Global context: this exercises main.run exactly like the CLI does (collect -> clean -> render),
but on a throwaway vault in pytest's tmp_path (https://docs.pytest.org/en/stable/how-to/tmp_path.html),
so the real notes and the real wordcloud.png are never touched.
"""

from vault_wordcloud.config import Config
from vault_wordcloud.main import run


def test_run_writes_png_and_counts_clean_words(tmp_path):
    vault = tmp_path / "vault"
    (vault / "Articles").mkdir(parents=True)
    # One top-level note and one article, both with markup that must not leak into the counts.
    (vault / "Home.md").write_text("---\naliases: [x]\n---\nInterpretability rocks. [[Home|exocortex]]", encoding="utf-8")
    (vault / "Articles" / "A.md").write_text("Interpretability again, see https://arxiv.org/abs/1", encoding="utf-8")

    config = Config(
        vault_dir=vault,
        source_files=["Home.md"],
        source_dirs=["Articles"],
        output=tmp_path / "cloud.png",
        log_dir=tmp_path / "logs",
        width=200,
        height=100,
        max_words=50,
        max_font_size=40,
        relative_scaling=0.5,
        random_state=0,
        extra_stopwords={"see"},
    )
    counts = run(config)

    assert config.output.exists() and config.output.stat().st_size > 0
    assert counts["Interpretability"] == 2  # counted once per note, case kept as written
    for junk in ("aliases", "https", "arxiv", "see", "Home"):
        assert junk not in counts
