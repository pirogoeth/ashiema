#!/usr/bin/env python

import hashlib

def get_connection():
    return _connection

def md5(data):
    _m = hashlib.md5()
    _m.update(data)
    return _m.hexdigest()