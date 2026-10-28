"""Phase 2: turn Obsidian-flavoured markdown into plain prose for word counting.

Global context: wordcloud tokenizes with the regex \\w[\\w']+ and counts everything it finds
(see WordCloud.process_text in https://github.com/amueller/word_cloud/blob/main/wordcloud/wordcloud.py).
So all markup that isn't text the reader sees gets removed here, before counting:
frontmatter, code, image embeds, link targets, URLs and HTML.
Syntax references: Obsidian internal links https://help.obsidian.md/Linking+notes+and+files/Internal+links,
Obsidian embeds https://help.obsidian.md/Linking+notes+and+files/Embed+files,
CommonMark links/images https://spec.commonmark.org/0.31.2/#links. Python `re`: https://docs.python.org/3/library/re.html
"""

import re

# (pattern, replacement) pairs applied in order; order matters because image syntax `![..](..)` also matches the plain-link pattern.
_RULES = [
    (re.compile(r"\A---\n.*?\n---\n", re.S), ""),  # YAML frontmatter: only at file start (\A), lazy .*? stops at the first closing ---
    (re.compile(r"```.*?```", re.S), " "),  # fenced code blocks: re.S lets . span newlines inside the fence
    (re.compile(r"!\[\[[^\]]*\]\]"), " "),  # Obsidian embeds ![[file|size]]: drop file names, hashes and sizes
    # Plain (non-embedded) links to image files, e.g. [[Images/<hash>_MD5.jpg|Open: Pasted image 2026….png]] written by
    # the local-images plugin: target and alias are file names, so drop the whole link before the wikilink rule keeps the alias.
    (re.compile(r"\[\[[^\]|]*\.(?:png|jpe?g|gif|webp|svg)(?:\|[^\]]*)?\]\]", re.I), " "),
    (re.compile(r"!\[[^\]]*\]\([^)]*\)"), " "),  # markdown images ![alt](url): alt text is usually empty or a file name
    (re.compile(r"\[([^\]]*)\]\([^)]*\)"), r"\1"),  # markdown links [text](url): keep the visible text (group 1), drop the url
    (re.compile(r"https?://\S+|www\.\S+"), " "),  # bare URLs: \S+ eats up to the next whitespace
    (re.compile(r"<[^>]+>"), " "),  # HTML tags such as <iframe ...> or <br>
]
# [[target#heading|alias]] -> alias if present, else target; group 1 = target(#heading), group 2 = optional alias.
_WIKILINK = re.compile(r"\[\[([^\]|]*)(?:\|([^\]]*))?\]\]")


def clean_markdown(text: str) -> str:
    """Return the reader-visible prose of one note, with markup stripped and apostrophes normalized."""
    text = text.replace("\r\n", "\n").replace("’", "'")  # CRLF -> LF so the anchored regexes match; ’ -> ' so STOPWORDS like "i'm" match
    for pattern, replacement in _RULES:
        text = pattern.sub(replacement, text)
    # A function replacement picks the alias when present, otherwise turns "Note#Heading" into "Note Heading" (re.sub with callable: https://docs.python.org/3/library/re.html#re.sub).
    text = _WIKILINK.sub(lambda m: m.group(2) or m.group(1).replace("#", " "), text)
    return text.strip()
