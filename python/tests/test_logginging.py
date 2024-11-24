import logging
from io import StringIO

from pythonning.logginging import ColoredFormatter
from pythonning.logginging import LogColor


def test_ColoredFormatter():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    formatter = ColoredFormatter(
        fmt="{level_color}{levelname}{red}red {message}",
        style="{",
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger = logging.getLogger("test_ColoredFormatter")
    logger.addHandler(handler)

    logger.info("TEST INFO message")
    logger.error("TEST ERROR message")
    logger.info(
        "hey {blue}this should be blue{reset} but not this",
        extra={"resolve_color": True},
    )

    info_color = ColoredFormatter.COLOR_BY_LEVEL[logging.INFO]
    result = stream.getvalue().split("\n")
    expected = (
        f"{info_color.value}INFO{LogColor.red.value}red hey "
        f"{LogColor.blue.value}this should be blue{LogColor.reset.value} "
        f"but not this{LogColor.reset.value}"
    )
    assert result[-2] == expected
