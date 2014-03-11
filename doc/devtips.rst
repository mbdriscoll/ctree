.. devtips:

Ctree Development Tips
======================

Using VirtualEnv
----------------

If you want to switch between multiple versions of Python, and/or keep ctree dependences out of your system site-packages, you can use virtualenv to create standalone python installations and switch between them easily.

To get started, install ``virtualenv`` using ``pip``::

        pip-2.7 install virtualenv

Then, create a virtual environment. We have a ``.gitignore`` entry in place to ignore ``venv-*`` directories::

        cd $CTREE
        virtualenv-2.7 venv-2.7

Use ``activate`` to switch to the new installation::

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
