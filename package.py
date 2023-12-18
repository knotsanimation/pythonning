name = "pythonning"

version = "1.5.0"

authors = ["Liam Collod"]

description = "Low-level python functions commonly used by any kind of developer."

uuid = "446add5adac048399303292b90c32c59"

requires = [
    "python-3+",
]

private_build_requires = [
    "python-3+",
]

build_command = "python {root}/build.py"

__test_command_base = (
    "pytest-launcher {root}/python/tests"
    " --config-file '${{PYTEST_CONFIG_FILE}}'"
    " --log-cli-level '${{PYTEST_LOG_CLI_LEVEL}}'"
)

tests = {
    "unit-37": {
        "command": __test_command_base,
        "requires": ["python-3.7", "pytest", "pytest_utils"],
    },
    "unit-39": {
        "command": __test_command_base,
        "requires": ["python-3.9", "pytest", "pytest_utils"],
    },
    "unit-310": {
        "command": __test_command_base,
        "requires": ["python-3.10", "pytest", "pytest_utils"],
    },
}

cachable = True


tools = [
    "pythonning-download-clearcache",
]


def commands():
    env.PYTHONPATH.append("{root}/python")

    alias(
        "pythonning-download-clearcache",
        "python -c 'import pythonning.web.download;pythonning.web.download.clear_download_cache()'",
    )
