Developing
==========

Documentation for maintaining the repository.

running tests
-------------

with rez
________

.. code-block:: shell

    cd {repo-root}
    # ensure package is build first
    rez-build -i

    rez-test pythonning

Running a specific tests:

.. code-block:: shell

    # only run the tests for python 3.9 defined in the package.py
    rez-test pythonning unit-39

with pip
________

.. code-block:: shell

   cd {repo-root}
   pip install .[test]
   pytest ./tests


building documentation
----------------------

.. code-block:: shell

    cd {repo-root}
    # ensure package is built first (necessary for autodoc)
    rez-build -i
    rez env sphinx furo pythonning
    python ./doc/build-doc.py -a

The documentation can then be found in ``./doc/build/html/index.html``

.. note::
    You only need to rez-build/rez-env when you change python file of pythonning.
    You can just successively call ``build-doc.py`` when only the doc is modified.

deploying documentation
-----------------------

Deploy the documentation to GitHub pages.

.. important::
    At Knot this process is automated during rez-release and does not need
    to be executed manually.


You must:

* have ``git`` installed on your system
* be on main branch
* have no uncommited changes
* have pushed the branch

.. code-block:: shell

    cd .
    # ensure package is built first (necessary for autodoc)
    rez-build -i
    rez-env sphinx furo pythonning
    python ./doc/publish-doc.py
