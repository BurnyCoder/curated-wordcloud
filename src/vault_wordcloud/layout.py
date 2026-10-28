"""Center-out word placement: each word goes to the free spot nearest the canvas centre.

Global context: wordcloud already places words largest-first, but it drops each one at a *uniformly random* free
spot (IntegralOccupancyMap.sample_position -> Cython query_integral_image,
https://github.com/amueller/word_cloud/blob/main/wordcloud/query_integral_image.pyx), so the biggest words can land
on the edges. Wordle and d3-cloud instead start every word at the centre and walk an elliptical Archimedean spiral
outward until it no longer collides (https://github.com/jasondavies/d3-cloud/blob/master/index.js, algorithm by
Jonathan Feinberg), which puts the biggest words in the middle. This class keeps the library's integral-image
collision test and picks the free position nearest the centre: the spot a fine-grained spiral search reaches first.
"""

import numpy as np
from wordcloud.wordcloud import IntegralOccupancyMap


class CenteredOccupancyMap(IntegralOccupancyMap):
    """IntegralOccupancyMap whose sample_position returns the free box closest to the canvas centre."""

    def sample_position(self, size_x, size_y, random_state):
        """Return the top-left (row, col) of the free size_x-by-size_y box nearest the centre, or None if none fits.

        random_state is unused: placement is deterministic, while word orientation stays seeded by the library.
        """
        ii = self.integral.astype(np.int64)  # int64 so the +/- below can't wrap around the way uint32 would
        # Box sum for every top-left (i, j) at once, using the same integral-image formula and the same ranges
        # (i < H - size_x, j < W - size_y) as the Cython loop. Summed-area tables: https://en.wikipedia.org/wiki/Summed-area_table
        area = ii[:-size_x, :-size_y] + ii[size_x:, size_y:] - ii[size_x:, :-size_y] - ii[:-size_x, size_y:]
        free = area == 0  # a box is free when no occupied pixel falls inside it
        if not free.any():
            return None  # lets the library rotate or shrink the word and retry, as it does with the original map
        # Squared distance of each box centre from the canvas centre, with rows scaled by height and cols by width.
        # The resulting ellipse has the canvas's aspect ratio, like d3-cloud's spiral that stretches x by width/height.
        rows = ((np.arange(free.shape[0]) + size_x / 2 - self.height / 2) / self.height) ** 2
        cols = ((np.arange(free.shape[1]) + size_y / 2 - self.width / 2) / self.width) ** 2
        dist = np.where(free, rows[:, None] + cols[None, :], np.inf)  # occupied spots can never win the argmin
        i, j = np.unravel_index(np.argmin(dist), dist.shape)  # flat argmin -> (row, col); ties go to the first index
        return int(i), int(j)
