"""Phase 3: count words and draw the cloud with the `wordcloud` library.

Global context: this is the official two-step path inside WordCloud.generate_from_text
(process_text -> generate_from_frequencies, https://github.com/amueller/word_cloud/blob/main/wordcloud/wordcloud.py),
done by hand so the raw counts can be returned and logged. Three changes from the library defaults: words are
placed centre-out (layout.CenteredOccupancyMap), sizes start from a fixed max_font_size with a flatter
relative_scaling, and every word gets a random rainbow hue. Parameter meanings:
https://amueller.github.io/word_cloud/generated/wordcloud.WordCloud.html ; minimal usage:
https://github.com/amueller/word_cloud/blob/main/examples/simple.py
"""

from unittest.mock import patch

import wordcloud.wordcloud as wordcloud_module
from wordcloud import STOPWORDS, WordCloud

from vault_wordcloud.config import Config
from vault_wordcloud.layout import CenteredOccupancyMap


def rainbow_color(*args, random_state, **kwargs) -> str:
    """Pick a random hue from the whole 0-359 spectrum at fixed saturation and lightness.

    Same call signature as the library's colour functions (word, font_size, position, orientation, random_state,
    font_path); only the seeded random_state is used, so reruns give the same colours. 45% lightness keeps yellow and
    cyan readable on white. The library's own random_color_func only draws hues 0-255, which skips pinks and magentas.
    Pillow parses hsl() strings: https://pillow.readthedocs.io/en/stable/reference/ImageColor.html
    """
    return f"hsl({random_state.randint(0, 359)}, 85%, 45%)"


def display_case(word: str) -> str:
    """Lowercase every token of a word or bigram except all-caps acronyms: "Artificial Intelligence" -> "artificial
    intelligence", "AI system" -> "AI system". Counting is already case-insensitive (the library merges case variants
    and shows the most common one); this only makes the shown form uniform."""
    return " ".join(token if token.isupper() else token.lower() for token in word.split(" "))


def render_wordcloud(text: str, config: Config) -> dict[str, int]:
    """Draw `text` into config.output as a PNG and return the word -> count dict the cloud was sized by."""
    cloud = WordCloud(
        width=config.width,
        height=config.height,
        max_words=config.max_words,
        # Fixed start size for the top word; skips the library's auto-fit of the top two words, which made "AI" ~660 px tall.
        max_font_size=config.max_font_size,
        # Each size is (rs * freq_ratio + 1 - rs) * previous size, roughly size ~ freq**rs; lower rs = flatter sizes.
        relative_scaling=config.relative_scaling,
        random_state=config.random_state,  # seeds word orientation and colours, so reruns are identical
        stopwords=STOPWORDS | config.extra_stopwords,  # library's English list plus vault-specific filler words
        min_word_length=2,  # drops one-letter leftovers like the "e" and "g" of "e.g." while keeping "AI"
        background_color="white",
        color_func=rainbow_color,
        collocations=True,  # default: also counts strong bigrams like "mechanistic interpretability" as one entry
    )
    # process_text tokenizes, drops stopwords/numbers/short words, merges case variants and plurals, and finds bigrams.
    # Its keys are unique ignoring case, so re-casing them with display_case can't merge two entries.
    counts = {display_case(word): n for word, n in cloud.process_text(text).items()}
    # generate_from_frequencies builds its occupancy map from the module-global name IntegralOccupancyMap, so swap in
    # the centre-out version for this call only; patch.object restores the original afterwards
    # (https://docs.python.org/3/library/unittest.mock.html#patch-object).
    with patch.object(wordcloud_module, "IntegralOccupancyMap", CenteredOccupancyMap):
        cloud.generate_from_frequencies(counts)  # lays out words sized by count, largest first
    config.output.parent.mkdir(parents=True, exist_ok=True)
    cloud.to_file(str(config.output))  # renders via Pillow and saves; format inferred from the .png suffix
    return counts
