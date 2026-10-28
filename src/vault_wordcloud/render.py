"""Phase 3: count words and draw the cloud with the `wordcloud` library.

Global context: this is the official two-step path inside WordCloud.generate_from_text
(process_text -> generate_from_frequencies, https://github.com/amueller/word_cloud/blob/main/wordcloud/wordcloud.py),
done by hand so the raw counts can be returned and logged. Parameter meanings:
https://amueller.github.io/word_cloud/generated/wordcloud.WordCloud.html ; minimal usage:
https://github.com/amueller/word_cloud/blob/main/examples/simple.py
"""

from wordcloud import STOPWORDS, WordCloud

from vault_wordcloud.config import Config


def render_wordcloud(text: str, config: Config) -> dict[str, int]:
    """Draw `text` into config.output as a PNG and return the word -> count dict the cloud was sized by."""
    cloud = WordCloud(
        width=config.width,
        height=config.height,
        max_words=config.max_words,
        random_state=config.random_state,  # seeds word placement and the colour function, so reruns are identical
        stopwords=STOPWORDS | config.extra_stopwords,  # library's English list plus vault-specific filler words
        min_word_length=2,  # drops one-letter leftovers like the "e" and "g" of "e.g." while keeping "AI"
        background_color="white",
        colormap="viridis",  # perceptually uniform matplotlib map (https://matplotlib.org/stable/users/explain/colors/colormaps.html)
        collocations=True,  # default: also counts strong bigrams like "mechanistic interpretability" as one entry
    )
    counts = cloud.process_text(text)  # tokenizes, drops stopwords/numbers/short words, merges plurals and finds bigrams
    cloud.generate_from_frequencies(counts)  # lays out words sized by count (exactly what generate() does internally)
    config.output.parent.mkdir(parents=True, exist_ok=True)
    cloud.to_file(str(config.output))  # renders via Pillow and saves; format inferred from the .png suffix
    return counts
