.. pythonning documentation master file, created by
   sphinx-quickstart on Sun Jan 14 19:54:54 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

pythonning
==========

``pythonning`` is a low-level module providing convenient functions and components
when working with python.

**intentions**

The intention is that you could share this module with anyone
that have **just python** installed and it will work. Anyone meaning
a friend, a data-sciencist, a random internet-people, ...

**prerequisites**

It is possible some functions have implicit requirements, meaning they except
some software to be on the machine of the user to work. But implicit means
that it doesn't prevent to import the library and use other functions.

An example would be a function related to git, to get a commit hash. You need
git on your system, but you can still call the function even if you don't have
git installed.

Keep in mind that even if a requirement is implicit for a piece of code,
we might have other better-suited package to store that code.

Contents
--------

.. toctree::
   :maxdepth: 2

   developing
   public-api


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
