"""
A setuptools based setup module to install the package with pip.

Generated from https://github.com/pypa/sampleproject.
"""

# XXX: keep in sync with package.py

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import pathlib

THISDIR = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (THISDIR / "README.md").read_text(encoding="utf-8")

setup(
    name="pythonning",
    version="1.9.0",
    description="Low-level python functions commonly used by any kind of developer.",  # Optional
    long_description=long_description,  # Optional
    long_description_content_type="text/markdown",  # Optional
    url="https://github.com/knotsanimation/pythonning",  # Optional
    author="Liam Collod",  # Optional
    author_email="monsieurlixm@gmail.com",  # Optional
    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 3 - Alpha",
        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords="basic, toolbox",  # Optional
    package_dir={"": "python"},  # Optional
    packages=find_packages(where="python"),  # Required
    # https://packaging.python.org/guides/distributing-packages-using-setuptools/#python-requires
    python_requires=">=3.7",
    # https://packaging.python.org/discussions/install-requires-vs-requirements/
    install_requires=[""],  # Optional
    # used via `pip install sampleproject[dev]`
    extras_require={  # Optional
        "dev": ["black"],
        "test": [
            "pytest>=7",
        ],
        "doc": [
            "sphinx==7.2.*",
            "furo==2023.9.*",
        ],
    },
    # https://packaging.python.org/specifications/core-metadata/#project-url-multiple-use
    project_urls={  # Optional
        "Bug Reports": "https://github.com/knotsanimation/pythonning/issues",
        "Source": "https://github.com/knotsanimation/pythonning/",
    },
)
