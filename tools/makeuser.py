#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import os, hashlib, shelve

db_file = os.getcwd() + "/../plugins/IdentificationPlugin/users"

username = raw_input("username: ")
password = raw_input("password: ")
level = int(raw_input("permission level: "))

m = hashlib.md5()
m.update(password)
del password
password = m.hexdigest()

if level not in xrange(0, 3):
    print "incorrect permission level. must be between 0 and 2"
    exit()

user = {
    username:
        {
            "password": password,
            "level": level
        }
    }

db = shelve.open(db_file)
db.update(user)
db.sync()
db.close()

print user
exit()
    