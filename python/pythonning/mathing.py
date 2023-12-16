import logging

LOGGER = logging.getLogger(__name__)


def remap_range(
    value: float,
    source_min: float,
    source_max: float,
    target_min: float,
    target_max: float,
) -> float:
    """
    Convert the range of the source to the given target range.

    Example::

        >>> remap_range(0.5, 0, 1, -10, 10)
        0.0

    Args:
        value: value to remap
        source_min: minimum value of the source range
        source_max: maximum value of the source range
        target_min: minimum value of the target range
        target_max: maximum value of the target range

    Returns:
        value remapped
    """
    normalized = (value - source_min) / (source_max - source_min)
    return (target_max - target_min) * normalized + target_min
