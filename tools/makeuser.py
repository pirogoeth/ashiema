#!/usr/bin/env python

import os, hashlib, shelve

db_file = os.getcwd() + "/../etc/users.db"

username = raw_input("username: ")
password = raw_input("password: ")
level = int(raw_input("permission level: "))

m = hashlib.md5()
m.update(password)
del password
password = m.hexdigest()

if level not in xrange(0, 4):
    print "incorrect permission level. must be between 0 and 3"
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
    