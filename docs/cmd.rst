Command Line Usage
==================

The main way to use AxiBot is the ``axibot`` command-line utility. Some examples are shown here. You can also see the utility itself for more info::

    $ axibot -h


Manual Control
--------------

Issue single manual commands::

    $ axibot manual pen_up 1000
    $ axibot manual disable_motors

Enter a shell to use the same commands::

    $ axibot manual
    (axibot) pen_down 1000
    (axibot) xy_move 400 400 100


File Estimation
---------------

Print info about the motion plan that would be used to plot an SVG file::

    $ axibot info examples/worldmap.svg

Plotting
--------

Actually plot an SVG file::

    $ axibot plot examples/worldmap.svg

By default, this will use an interface interface to prompt certain user actions.

Web Server
----------

To start a webserver for remote control of the AxiDraw::

    $ axibot server
