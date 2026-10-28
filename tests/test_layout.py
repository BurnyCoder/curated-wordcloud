"""Tests for center-out word placement (layout.py) and the rainbow colour function (render.py).

Global context: CenteredOccupancyMap replaces wordcloud's uniform-random spot picker with "nearest free spot to the
centre", the Wordle/d3-cloud recipe (https://github.com/jasondavies/d3-cloud). Occupancy is set through the
library's own IntegralOccupancyMap.update, so these tests also pin the integral-image index convention:
a position (i, j) covers rows i+1..i+sx and cols j+1..j+sy, exactly like wordcloud's query_integral_image.
"""

import re
from random import Random

import numpy as np
from PIL import ImageColor

from vault_wordcloud.layout import CenteredOccupancyMap
from vault_wordcloud.render import rainbow_color


def _map(occupied: np.ndarray) -> CenteredOccupancyMap:
    """Build a 100x200 map and mark `occupied` pixels via the library's update (cumsum from (0, 0))."""
    occupancy = CenteredOccupancyMap(100, 200, None)
    occupancy.update(occupied.astype(np.uint32), 0, 0)
    return occupancy


def test_empty_map_places_box_dead_centre():
    # Box centre = (i + 10/2, j + 20/2) must equal the canvas centre (50, 100).
    assert CenteredOccupancyMap(100, 200, None).sample_position(10, 20, Random(0)) == (45, 90)


def test_occupied_centre_gives_nearest_free_neighbour():
    img = np.zeros((100, 200))
    img[40:60, 80:120] = 255  # block the centre, like an already placed big word
    i, j = _map(img).sample_position(10, 20, Random(0))
    assert img[i + 1 : i + 11, j + 1 : j + 21].sum() == 0  # the chosen box is free
    # Nearest in aspect-normalized distance: just below the block, horizontally centred
    # (below beats above by one pixel because boxes cover rows i+1..i+sx).
    assert (i, j) == (59, 90)


def test_returns_none_when_nothing_fits():
    assert CenteredOccupancyMap(100, 200, None).sample_position(100, 10, Random(0)) is None  # taller than canvas
    assert _map(np.full((100, 200), 255)).sample_position(5, 5, Random(0)) is None  # canvas full


def test_rainbow_color_full_spectrum_hsl_and_seeded():
    colour = rainbow_color("AI", 10, (0, 0), None, random_state=Random(1))
    hue = int(re.fullmatch(r"hsl\((\d+), 85%, 45%\)", colour).group(1))
    assert 0 <= hue < 360
    assert ImageColor.getrgb(colour)  # Pillow can parse it (https://pillow.readthedocs.io/en/stable/reference/ImageColor.html)
    assert rainbow_color("AI", 10, (0, 0), None, random_state=Random(1)) == colour  # same seed -> same colour
