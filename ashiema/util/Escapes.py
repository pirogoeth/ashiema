#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

# line style
NL          = "\x0a"
# text style
NONE        = "\x15"
BOLD        = "\x02"
ITALIC      = "\x29"
UNDERLINE   = "\x31"
COLOURED    = "\x03"
FIXED_PITCH = "\x17"
REVERSE     = "\x18"
# text colour
WHITE       = COLOURED + "0"
BLACK       = COLOURED + "1"
DARK_BLUE   = COLOURED + "2"
GREEN       = COLOURED + "3"
RED         = COLOURED + "4"
DARK_RED    = COLOURED + "5"
PURPLE      = COLOURED + "6"
GOLD        = COLOURED + "7"
YELLOW      = COLOURED + "8"
LIGHT_GREEN = COLOURED + "9"
LIGHT_BLUE  = COLOURED + "10"
AQUA        = COLOURED + "11"
BLUE        = COLOURED + "12"
PINK        = COLOURED + "14"
GREY        = COLOURED + "15"