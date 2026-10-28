"""Unit tests for clean_markdown: Obsidian markdown in, plain prose out.

Global context: the word cloud counts every token it sees, so any markup left over
(URLs, image hashes, link targets) would show up as fake "words". These tests pin
down exactly which syntax is dropped and which human-readable text is kept.
Obsidian link syntax: https://help.obsidian.md/Linking+notes+and+files/Internal+links
"""

from vault_wordcloud.clean import clean_markdown


def test_strips_yaml_frontmatter_but_keeps_body():
    # Frontmatter is the `---`-fenced YAML block at the very top of a note (https://help.obsidian.md/Editing+and+formatting/Properties).
    out = clean_markdown("---\naliases:\n  - Exobrain\n---\nHai there!")
    assert "aliases" not in out and "Exobrain" not in out
    assert "Hai there!" in out


def test_handles_windows_line_endings_in_frontmatter():
    # Notes edited on Windows may use CRLF; the frontmatter regex must still match.
    assert "aliases" not in clean_markdown("---\r\naliases: x\r\n---\r\nBody")


def test_removes_image_embeds_entirely():
    # Embeds like ![[Images/<hash>_MD5.jpeg|200]] carry only file names and sizes, never prose.
    out = clean_markdown("A ![[Images/dd8e_MD5.jpeg|200]] B ![alt](https://x.org/y.png) C")
    for junk in ("Images", "MD5", "jpeg", "200", "alt", "png", "x.org"):
        assert junk not in out
    assert out.split() == ["A", "B", "C"]


def test_wikilink_alias_wins_over_target():
    # [[target|alias]] renders as "alias" in Obsidian, so the alias is what the reader sees.
    out = clean_markdown("Writing in [[Home|exocortex]] daily")
    assert "exocortex" in out and "Home" not in out


def test_wikilink_without_alias_keeps_target_and_heading_words():
    # [[Note#Heading]] renders as "Note > Heading"; keep both as words, drop the '#'.
    out = clean_markdown("See [[Physics#Quantum gravity]] now")
    assert "#" not in out
    assert out.split() == ["See", "Physics", "Quantum", "gravity", "now"]


def test_markdown_link_keeps_text_drops_url():
    out = clean_markdown("[Bitter lesson - Wikipedia](https://en.wikipedia.org/wiki/Bitter_lesson)")
    assert "Bitter lesson - Wikipedia" in out
    assert "wikipedia.org" not in out and "https" not in out


def test_removes_bare_urls():
    out = clean_markdown("read https://arxiv.org/abs/2604.21691 and www.example.com today")
    assert out.split() == ["read", "and", "today"]


def test_removes_code_fences_and_html():
    out = clean_markdown("before\n```python\nimport os\n```\n<iframe src=\"x\"></iframe>after")
    assert "import" not in out and "iframe" not in out
    assert out.split() == ["before", "after"]


def test_drops_czech_lines_keeps_english_ones():
    # Lines with Czech-only letters (ě š č ř ž ů ň ť ď) are removed whole; English lines around them survive.
    out = clean_markdown("Work in progress article.\nŘeší se to pořád všechny ty roky.\nBut researchers disagree.")
    assert out.split() == ["Work", "in", "progress", "article.", "But", "researchers", "disagree."]


def test_normalizes_typographic_apostrophes():
    # wordcloud's STOPWORDS spell contractions with a straight ' (e.g. "i'm"), but the vault uses ’ (smart-typography plugin).
    assert clean_markdown("I’m sure it’s fine") == "I'm sure it's fine"
