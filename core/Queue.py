#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

""" this implements a FIFO queue for use by the select loop in Connection.py """

class Queue(object):
    def __init__(self, maxsize = 0):
        self._queue = []
        self._maxsize = maxsize
    
    def __repr__(self):
        return "<Queue(%d)>" % (len(self._queue))
    
    def append(self, data):
        """ wrapper for insert """
        
        self.insert(data, index = None)

    def insert(self, data, index = None):
        """ will automatically insert at the end if index is not given """
        if len(self._queue) == self._maxsize and self._maxsize is not 0:
            raise QueueError("Queue has reached maxsize of %d" % (self._maxsize))
        if index is not None and isinstance(index, int):
            self._queue.insert(data, index = index)
        else: self._queue.append(data)
    
    def pop(self, index = None):
        """ will automatically return the first item from the queue and then remove from the queue. """
        if len(self._queue) is 0:
            raise QueueError("Queue is empty.")
        if index is not None and isinstance(index, int):
            return self._queue.pop(index)
        else: return self._queue.pop(0)
    
    def count(self):
        """ returns the count of the queue """
        return len(self._queue)
    
    def clear(self):
        """ clears the entire queue out """
        self._queue = []

class QueueError(Exception):
    """ raised when an error occurs with the queue """
    
    def __init__(self, message = None):
        self.message = message

    def __repr__(self):
        return repr(self.message)

    def __str__(self):
        return self.__repr__()