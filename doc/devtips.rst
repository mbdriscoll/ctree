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


Cleaning the Folder of Temporary Files
--------------------------------------

If ``ctree`` is exiting uncleanly it may leave compilation directories in the temporary folder. If there are lots of them, ``rm`` may not be sufficient to remove them::

    $ CTREE_TMP_DIR=/var/folders/k3/_z9txmtx3vd1t_64hbx9y4qr0000gn/T
    $ rm -rf $CTREE_TMP_DIR/ctree-*
    zsh: argument list too long: rm

Use a command like the following to rememdy the situation::

    $ find $CTREE_TMP_DIR -name "ctree-*" | xargs rm -rf
