# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013-2015 Sean Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import glob, os

from ashiema import api
from ashiema import irc
from ashiema import plugin
from ashiema import util

modules = glob.glob(os.path.dirname(__file__) + "/*.py")
__all__ = [os.path.basename(f)[:-3] for f in modules
           if not os.path.basename(f).startswith('_') and
           not f.endswith('__init__.py') and os.path.isfile(f)]

__version__ = "1.1-dev"

config = None

