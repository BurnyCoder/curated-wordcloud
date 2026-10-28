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
        ii = self.integral  # uint32; no int64 copy needed: see the overflow note below
        # Box sum for every top-left (i, j) at once, using the same integral-image formula and the same ranges
        # (i < H - size_x, j < W - size_y) as the Cython loop. Summed-area tables: https://en.wikipedia.org/wiki/Summed-area_table
        # Intermediate uint32 +/- may wrap, but the true sum is <= 255*H*W < 2**32 (canvases up to ~16.8 MP), and
        # modular arithmetic then lands on the exact value (numpy integer overflow wraps: https://numpy.org/doc/stable/user/basics.types.html#overflow-errors).
        area = ii[:-size_x, :-size_y] + ii[size_x:, size_y:] - ii[size_x:, :-size_y] - ii[:-size_x, size_y:]
        free = np.flatnonzero(area == 0)  # flat indices of boxes with no occupied pixel, in row-major order
        if not free.size:
            return None  # lets the library rotate or shrink the word and retry, as it does with the original map
        i, j = np.divmod(free, area.shape[1])  # flat index -> (row, col) of each free box's top-left corner
        # Squared distance of each free box's centre from the canvas centre, with rows scaled by height and cols by
        # width. The resulting ellipse has the canvas's aspect ratio, like d3-cloud's spiral that stretches x by width/height.
        dist = ((i + size_x / 2 - self.height / 2) / self.height) ** 2 + ((j + size_y / 2 - self.width / 2) / self.width) ** 2
        k = np.argmin(dist)  # nearest free box; ties go to the first in row-major order
        return int(i[k]), int(j[k])
