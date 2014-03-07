.. install:

Ctree Installation
==================

Dependencies
------------

* Install `Python 2.7.x <http://python.org/>`_.
* Install `Clang and LLVM 3.3 <http://llvm.org/>`_.
* Install `llvmpy <http://www.llvmpy.org/>`_.

Building ctree
--------------

Ctree is available from GitHub and must be built from source:

.. code-block:: sh

   $ git clone git@github.com:ucb-sejits/ctree.git
   $ cd ctree
   $ python setup.py install

To verify your installation, install nose:

.. code-block:: sh

   $ pip install nose

And run nosetests:


.. code-block:: sh

   $ nosetests
   ......................................................................
   ....S...............................................S.S...............
   ......................................................................
   ......
   ----------------------------------------------------------------------
   Ran 216 tests in 1.220s

   OK (SKIP=3)
