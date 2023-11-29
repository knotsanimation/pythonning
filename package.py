name = "pythonning"

version = "0.1.0"

authors = ["Liam Collod"]

description = "Low-level python functions commonly used by any kind of developer."

uuid = "446add5adac048399303292b90c32c59"

requires = [
    "python-3+",
]

private_build_requires = ["python-3+"]

build_command = "python {root}/build.py"

tools = []


def commands():
    env.PYTHONPATH.append("{root}/python")
