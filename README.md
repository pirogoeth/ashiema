ashiema
=======

IRC bot written in python with an event driven framework.

Running The Bot
===============

After modifying your example.conf and renaming it to whatever you may wish, you can run the bot simply by typing ```python ./ashiema.py <confname>``` into your console.  

**NOTE**: I know for sure that this bot will work on Linux and BSD operating systems, but I have not the slightest clue if it will run on Windows.

Writing Plugins
===============

Ashiema has a fairly simple and straightforward plugin framework. It is pretty easy to write a new plugin and extend the functionality of your bot.

As with any python class you will write, you must start with your imports, but you must also import certain parts of ashiema's core.  

```python
from core import CorePlugin, Event, HelpFactory, get_connection, util
from core.util import Escapes # You only need the Escapes class if you plan on colouring/using formatting (bold, etc) on your messages
from core.CorePlugin import Plugin
from core.Event import Event
from core.HelpFactory import Contexts
from core.HelpFactory import CONTEXT, DESC, PARAMS
```

Then, define your class and inherit the ```Plugin``` class.

```python
class ExamplePlugin(Plugin):
    ...
```

Define your init and teardown methods.

```python
    def __init__(self, connection, eventhandler):
        Plugin.__init__(self, connection, eventhandler, needs_dir = <boolean>)
        ...

    def __deinit__(self):
        ...
```

**Note about needs_dir**: the ```needs_dir``` parameter can be set in your init method, and a directory will be created in plugins/ for you to store data into.

You will use your init/deinit methods to handle any registration/deregistration with the eventhandler, as well as any other set up you will need to do.

To use the eventhandler, you must call ``self.eventhandler.get_events()[EventName].register(self.method_handler)``.

So, to register for MessageEvents, you would use:

```python
self.eventhandler.get_events()['MessageEvent'].register(self.handler)
```

And to deregister:

```python
self.eventhandler.get_events()['MessageEvent'].deregister(self.handler)
```

Below your plugin class, **you MUST** add a ```__data__``` dictionary that provides information about the plugin, which looks like the following:

```python
__data__ = {
    'name'      : 'SomePlugin',
    'version'   : 'x.y',
    'require'   : ['NameOfFirstRequiredPlugin', 'NameOfSecondRequiredPlugin', ...],
    'main'      : PluginClassName
}
```

The ```__data__``` dictionary **MUST** be at the bottom of your file below the class.

Using Permissions
=================

Permission levels go from 0 to 2, with 2 being bot administrators.

To use permissions in your plugin, you must register for the PluginsLoadedEvent.

```python

class ExamplePermissions(Plugin):

    def __init__(self, connection, eventhandler):
        Plugin.__init__(self, connection, eventhandler, needs_dir = False)

        self.eventhandler.get_events()['MessageEvent'].register(self.handler)
        self.eventhandler.get_events()['PluginsLoadedEvent'].register(self.load_identification)

    def __deinit__(self, connection, eventhandler):
        self.eventhandler.get_events()['MessageEvent'].deregister(self.handler)
        self.eventhandler.get_events()['PluginsLoadedEvent'].deregister(self.load_identification)

    def load_identification(self):
        self.identification = get_connection().pluginloader.get_plugin('IdentificationPlugin')

    def handler(self, data):
        if data.message == (0, 'example'):
            assert self.identification.require_level(data, 2)
        elif data.message == (0, 'otherexample'):
            if self.identification.require_level(data, 2):
                do_something()
                ...
            else:
                data.origin.message("You do not have permission to use this function.")
                ...

__data__ = {
    'name'      : 'ExamplePermissions',
    'version'   : '1.0',
    'require'   : ['IdentificationPlugin'],
    'main'      : ExamplePermissions
}

__help__ = {
    'example' : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Does something.',
        PARAMS  : ''
    },
    'otherexample' : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Does something else.',
        PARAMS  : ''
    }
}
```

Submitting Data To The HelpFactory
==================================

All help data collection is done during load of all plugins.  A plugin is not required to provide command help, but it is recommended to do so.

Help data is specified by providing a ```__help__``` dictionary at the bottom of your plugin **below** the ```__data__``` dictionary.  Help data dictionary format is as shown:

```python
__help__ = {
    'command' : {
        CONTEXT : Contexts.PUBLIC **OR** Contexts.PRIVATE,
        DESC    : 'Command description',
        PARMAS  : '<string> <describing> <all> [params]'
    }
}
```

An example follows:

```python
__help__ = {
    'example' : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Does something.',
        PARAMS  : ''
    },
    'otherexample' : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Does something else.',
        PARAMS  : ''
    },
    'other' : {
        CONTEXT : Contexts.PRIVATE,
        DESC    : 'Does something privately.',
        PARAMS  : ''
    }
}
```

Catching Events
===============

Events are simple to catch, it's as simple as ```self.eventhandler.get_events()[EventName].register(self.handler_function)```.

Events provided by the system:

 - RFCEvent
 - PingEvent
 - ErrorEvent
 - ModeChangeEvent
 - MessageEvent
 - PMEvent
 - JoinEvent
 - PartEvent
 - QuitEvent
 - PluginsLoadedEvent

Creating And Firing Custom Events
=================================

The event system allows plugins to register and fire custom events as data comes through or as actions are performed.

A custom event should look as follows:

```python
class ExampleEvent(Event):

    def __init__(self, eventhandler):
        Event.__init__(self, eventhandler, "ExampleEvent")
        self.__register__()

    def match(self, data):
        """ This is where you should try and match the data given by the server, if that is what you're trying to do.  Otherwise, you can just **pass**. """
        
        pass

    def run(self, data):
        for callback in self.callbacks.values():
            callback(data)

class Example(Plugin):
    
    def __init__(self, connection, eventhandler):
        Plugin.__init__(self, connection, eventhandler, needs_dir = False)
        self.example_event = ExampleEvent()
        ...

    def handler(self, data):
        if (caught_some_data):
            self.eventhandler.fire_once(self.example_event, (event_data))
            ...
```

Contributing
============

If you wish to contribute to this project, make sure your changes follow the following conventions:

1. Use spaces, not tabs.  Spaces are much prettier.
2. When indenting, only use four spaces per "indention".
3. Use method_name, not methodName when naming methods/fields/etc.
4. When working with "private or protected" methods, use ```__method__``` or ```_method_```.
5. Make sure your code is readable enough that someone can determine what it does if you don't provide documentation with it.  If you provide docs, go crazy.

If you wish to contribute long-term to the project (eg., repo contributor..), send an email to <pirogoeth@maio.me> noting what you want and tell me why you want to help :)

If this readme is lacking any crucial information, file an issue stating what is wrong and I'll get right to fixing it.
