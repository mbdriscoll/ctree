.. watts up meter interactive shell:

Using a WattsUpMeter
===================================

``ctree`` includes support for a WattsUp? Pro meter.
For more information on this device see `watts up meters <https://www.wattsupmeters.com/secure/products.php?pn=0>`_

ctree supports the device directly with in it's autotuning.
Programmatic access to the device is included in the ctree.metrics package.

The device is finicky, it is sometimes useful to talk to the device directly through an
interactive shell in order to confirm it is working

Using the interactive shell
---------------

From the command line::


        ctree --wattsupmeter

or in the cast that the shell cannot guess the device name::


        ctree --wattsupmeter -p /dev/[name of usb device]


or directly (assuming you are in the ctree directory) via::


        python ctree/metrics/wattsupmeter.py -i


The interpreter has a simple list of commands that can be listed
via the help command.  Direct commands and their response can be typed
in at the prompt:  See
`watts up meter API <https://www.wattsupmeters.com/secure/downloads/CommunicationsProtocol090824.pdf>`_.

Usually the following commands are all it takes to see what's going on::


        record
        get_recording


The interpreter uses gnu getline so the standard arrow key magic is available.
