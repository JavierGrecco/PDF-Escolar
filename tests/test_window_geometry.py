"""Tests for screen-aware desktop window dimensions."""

import pytest

from pdf_escolar.ui.window_geometry import responsive_window_sizes


@pytest.mark.parametrize(
    ("screen_size", "preferred", "minimum"),
    [
        ((911, 512), (1180, 760), (880, 620)),
        ((1366, 728), (1180, 760), (880, 620)),
        ((1920, 1040), (1180, 760), (880, 620)),
        ((480, 320), (920, 780), (720, 600)),
    ],
)
def test_window_sizes_fit_available_screen(screen_size, preferred, minimum):
    (min_width, min_height), (width, height) = responsive_window_sizes(
        *screen_size,
        preferred_size=preferred,
        minimum_size=minimum,
    )
    width_limit = max(1, screen_size[0] - 40)
    height_limit = max(1, screen_size[1] - 72)

    assert 1 <= min_width <= width <= width_limit
    assert 1 <= min_height <= height <= height_limit


def test_large_screen_preserves_preferred_and_minimum_sizes():
    minimum, preferred = responsive_window_sizes(
        1920,
        1080,
        preferred_size=(1180, 760),
        minimum_size=(880, 620),
    )
    assert minimum == (880, 620)
    assert preferred == (1180, 760)


@pytest.mark.parametrize("screen_size", [(0, 600), (800, 0), (-1, 400)])
def test_window_sizes_reject_invalid_screen_dimensions(screen_size):
    with pytest.raises(ValueError, match="área disponible"):
        responsive_window_sizes(
            *screen_size,
            preferred_size=(920, 780),
            minimum_size=(720, 600),
        )
