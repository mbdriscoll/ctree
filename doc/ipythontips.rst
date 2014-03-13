.. ipython visualization:

Using iPython for AST Visualization
===================================

iPython provides a decent environment for visualizing the transformation of the abstract syntax trees
(AST) of the specializaed kernels.  Following these simple guidelines can make it easier to write and
debug the multiple node transformation passes that are necessary to implement a specialized kernel

Installing iPython
------------------

``ipython`` can be installed in several different ways depending on your platform:  See
`installing ipython <http://ipython.org/install.html>`_.  Just using ``pip`` seems to work
fine on OSX.

Starting iPython
----------------

In the shell::

        cd $CTREE
        ipython notebook

This will start an ``ipython`` server and open the dashboard window in the browser.  From the dashboard click
``New Notebook``.  You will add one or more sections of python code in cells on the ``notebook`` page.  The ``ipython``
interpreter for this page will be running just as if you had started the regular ``python`` interpereter.

Let's Visualize
---------------

In the first cell::

        import inspect, ast
tree1 = ast.parse(inspect.getsource(func))
from ctree.visual.dot_manager import DotManager






        source venv-2.7/bin/activate

Check out your new ``python`` and ``pip`` binaries::

        zsh% which python
        ./venv-2.7/bin/python

        zsh% which pip
        ./venv-2.7/bin/pip

Install ``ctree`` dependencies using the current ``pip``::

        pip install nose Sphinx numpy coverage
        cd $LLVMPY
        LLVM_CONFIG_PATH=... python setup.py install

Change back to the ``ctree`` directory and run the test suite to make sure everything is okay::

        cd $CTREE
        nosetests

To switch back to your default python installation, run::

        deactivate

You can re-activate the virtualenv at any time using::

        source venv-2.7/bin/activate
