"""Small helpers to size desktop windows to the available screen area."""

from __future__ import annotations

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget


def responsive_window_sizes(
    available_width: int,
    available_height: int,
    *,
    preferred_size: tuple[int, int],
    minimum_size: tuple[int, int],
    horizontal_margin: int = 40,
    vertical_margin: int = 72,
    minimum_width_floor: int = 520,
    minimum_height_floor: int = 360,
) -> tuple[tuple[int, int], tuple[int, int]]:
    """Return a feasible minimum and initial size for a screen work area.

    Qt sizes are expressed in logical pixels, so these values naturally follow
    the desktop's display scaling. On small screens the minimum size is reduced
    rather than forcing part of the window outside the visible work area.
    """
    if available_width < 1 or available_height < 1:
        raise ValueError("El área disponible de la pantalla debe ser positiva.")
    if any(value < 1 for value in (*preferred_size, *minimum_size)):
        raise ValueError("Los tamaños de ventana deben ser positivos.")

    width_limit = max(1, available_width - horizontal_margin)
    height_limit = max(1, available_height - vertical_margin)

    minimum_width = min(
        minimum_size[0],
        width_limit,
        max(minimum_width_floor, int(width_limit * 0.75)),
    )
    minimum_height = min(
        minimum_size[1],
        height_limit,
        max(minimum_height_floor, int(height_limit * 0.75)),
    )
    width = max(minimum_width, min(preferred_size[0], width_limit))
    height = max(minimum_height, min(preferred_size[1], height_limit))

    return (minimum_width, minimum_height), (width, height)


def requires_compact_layout(
    preferred_size: tuple[int, int],
    fitted_size: tuple[int, int],
) -> bool:
    """Return whether screen constraints forced either window dimension to shrink."""
    return any(actual < preferred for preferred, actual in zip(preferred_size, fitted_size))


def fit_window_to_screen(
    widget: QWidget,
    *,
    preferred_size: tuple[int, int],
    minimum_size: tuple[int, int],
    parent: QWidget | None = None,
) -> bool:
    """Fit a window to the work area and report whether compact layout is needed."""
    screen = parent.screen() if parent is not None else None
    if screen is None:
        screen = widget.screen()
    if screen is None:
        screen = QGuiApplication.primaryScreen()

    if screen is None:
        widget.setMinimumSize(*minimum_size)
        widget.resize(*preferred_size)
        return False

    area = screen.availableGeometry()
    fitted_minimum, fitted_preferred = responsive_window_sizes(
        area.width(),
        area.height(),
        preferred_size=preferred_size,
        minimum_size=minimum_size,
    )
    widget.setMinimumSize(*fitted_minimum)
    widget.resize(*fitted_preferred)
    return requires_compact_layout(preferred_size, fitted_preferred)
