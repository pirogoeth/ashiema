ashiema
=======

IRC bot written in python with an event driven framework.

Running The Bot
===============

Before you can run your bot, you must do the following:

```
cd tools
python ./makeuser.py
```

You will be presented with a prompt:

```
username: <your username>
password: <your password>
permission level: <0, 1, 2>
```

After you make your user account, you should start modifying your configurations!

After modifying your example.conf and renaming it to whatever you may wish, you can run the bot simply by typing `python ./ashiema.py <confname>` into your console.  

**NOTE**: I know for sure that this bot will work on Linux and BSD operating systems, but I have not the slightest clue if it will run on Windows.

Writing Plugins
===============

Ashiema has a fairly simple and straightforward plugin framework. It is pretty easy to write a new plugin and extend the functionality of your bot.

As with any python class you will write, you must start with your imports, but you must also import certain parts of ashiema's core.  

```
from ashiema import Plugin, Events, util
from ashiema.util import Escapes # You only need the Escapes class if you plan on colouring/using formatting (bold, etc) on your messages
from ashiema.Plugin import Plugin
from ashiema.HelpFactory import Contexts, CONTEXT, DESC, PARAMS, ALIASES
```

Then, define your class and inherit the `Plugin` class.

```
class ExamplePlugin(Plugin):
    ...
```

Define your init and teardown methods.

```
    def __init__(self):
        Plugin.__init__(self, needs_dir = <boolean>, needs_comm_pipe = <boolean>, needs_event_pipe = <boolean>)
        ...

    def __deinit__(self):
        ...
```

**Note about needs_dir**: the `needs_dir` parameter can be set in your init method, and a directory will be created in plugins/ for you to store data into.

You will use your init/deinit methods to handle any registration/deregistration with the eventhandler, as well as any other set up you will need to do.

To use the eventhandler, you must call `self.get_event(EventName).register(self.method_handler)`.

So, to register for MessageEvents, you would use:

```
self.get_event('MessageEvent').register(self.handler)
```

And to deregister:

```
self.get_event('MessageEvent').deregister(self.handler)
```

Below your plugin class, **you MUST** add a `__data__` dictionary that provides information about the plugin, which looks like the following:

```
__data__ = {
    'name'      : 'SomePlugin',
    'version'   : 'x.y',
    'require'   : ['NameOfFirstRequiredPlugin', 'NameOfSecondRequiredPlugin', ...],
    'main'      : PluginClassName,
    'events'    : [LocalEventClass1, LocalEventClass2, ...]
}
```

The `__data__` dictionary **MUST** be at the bottom of your file below the class.

Using Permissions
=================

Permission levels go from 0 to 2, with 2 being bot administrators.

To use permissions in your plugin, you must register for the PluginsLoadedEvent.

```

class PermissionsExample(Plugin):

    def __init__(self):

        Plugin.__init__(self, needs_dir = False, needs_comm_pipe = False)

        self.get_event('MessageEvent').register(self.handler)
        self.get_event('PluginsLoadedEvent').register(self.load_identification)

    def __deinit__(self):

        self.get_event('MessageEvent').deregister(self.handler)
        self.get_event('PluginsLoadedEvent').deregister(self.load_identification)

    def load_identification(self):

        self.identification = self.get_plugin('IdentificationPlugin')

    def handler(self, data):

        if data.message == (0, 'example'):
            assert self.identification.require_level(data, 2)
            ...
        elif data.message == (0, 'otherexample'):
            if self.identification.require_level(data, 2):
                do_something()
                ...
            else:
                ...

__data__ = {
    'name'      : 'PermissionsExample',
    'version'   : '1.0',
    'require'   : ['IdentificationPlugin'],
    'main'      : PermissionsExample,
    'events'    : []
}

__help__ = {
    'example' : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Does something.',
        PARAMS  : '',
        ALIASES : []
    },
    'otherexample' : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Does something else.',
        PARAMS  : '',
        ALIASES : []
    }
}
```

When writing permission restrictions for user-interactive commands, remember:

 - The `require_level()` method automatically sends messages to the user that the restriction is taking place on, so if you let them know that they lack permissions, you will actually be notifying them twice.
 - When the assertion that runs `require_level()` fails, it raises an AssertionError, which bubbles up and is displayed in logs, and should not affect code performance.
 - Permission levels only range from 0 to 2, so using anything outside of that range will raise an exception.
 - Assertions are the preferred way to enforce permissions with `require_level()`.

Submitting Data To The HelpFactory
==================================

All help data collection is done during load of all plugins.  A plugin is not required to provide command help, but it is recommended to do so.

Help data is specified by providing a `__help__` dictionary at the bottom of your plugin **below** the `__data__` dictionary.  Help data dictionary format is as shown:

```
__help__ = {
    'command' : {
        CONTEXT : Contexts.PUBLIC **OR** Contexts.PRIVATE,
        DESC    : 'Command description',
        PARAMS  : '<string> <describing> <all> [params]',
        ALIASES : ['aliases', 'for', 'this', 'command']
    }
}
```

An example follows:

```
__help__ = {
    'example' : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Does something.',
        PARAMS  : '',
        ALIASES : []
    },
    'otherexample' : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Does something else.',
        PARAMS  : '',
        ALIASES : []
    },
    'other' : {
        CONTEXT : Contexts.PRIVATE,
        DESC    : 'Does something privately.',
        PARAMS  : '',
        ALIASES : []
    }
}
```

Catching Events
===============

Events are simple to catch, it's as simple as `self.get_event(EventName].register(self.handler_function)`.

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

```
class ExampleEvent(Event):

    def __init__(self):

        Event.__init__(self, "ExampleEvent")
        self.__register__()

    def match(self, data):
        """ This is where you should try and match the data given by the server, if that is what you're trying to do.  
            Otherwise, you can just return False. """
        
        return False

    def run(self, data):

        for callback in self.callbacks.values():
            if self.is_cancelled():
                break
            else:
                callback(data)
```

If you are firing the event based on data retrieved in a handler:

```
class Example(Plugin):
    
    def __init__(self):

        Plugin.__init__(self, needs_dir = False, needs_comm_pipe = False, needs_event_pipe = False)
        ...

    def handler(self, data):

        if (caught_some_data):
            self.fire_event(self.example_event, (event_data))
            ...

__data__ = {
    ...
    'events'    : [ExampleEvent]
}
```

If all data is parsed through the connection data pipe, and you're waiting for feedback:

```
class ExamplePlugin(Plugin):

    def __init__(self):

        Plugin.__init__(self, needs_dir = False, needs_comm_pipe = False, needs_event_pipe = False)

        self.example_event = self.get_event('ExampleEvent').register(this.handler_function)
        ...
    
    def handler_function(self, data):

        if (...)
            ...
```

Trafficking Data Through Subprocesses (alpha)
=============================================

When writing plugins, there are certain cases where you will want to run jobs, process data, or run a service in a separate process to avoid bogging down the main loop.

For example, you are trying to write a plugin that listens for input through network channels, but running your listening loop inside the bot's event loop may add unnecessary overhead, causing the bot to slow down or become non-responsive if your listening loop starts blocking.
Since Python presents us with the wonderful GIL, basically denying us access to true multi-threaded capabilities, we use the [**multiprocessing**] [1] module to run code in a process that is **almost completely** isolated from the bot's main operations.

The downside of using subprocesses inside modules is the fact that there's not a particularly easy way to communicate data that is gathered back into the main process.

To provide a way of sending data through the server, the plugin framework provides a [communication pipeline] [2] in the form of a unidirectional [multiprocessing.Pipe] [3] pair.
The communication pipeline allows the sending of data from a separate process straight to the Connection object's data queue.  Data in the comm. pipeline is processed every time the main event loop ticks (goes through one cycle).

To be allowed direct access to the comm. pipe from your plugin, you must add `needs_comm_pipe = True` to the superclass constructor call at the top of your plugin. An example follows.

```
class ExamplePlugin(Plugin):

    def __init__(self):

        Plugin.__init__(self, needs_dir = False, needs_comm_pipe = True, needs_event_pipe = False)

        ...

    def __start(self, *args):

        class ExamplePluginSubprocess(multiprocessing.Process):

            def __init__(self, plugin, *args):

                Process.__init__(self, name = "ExamplePluginSubprocess")
                
                self.plugin = plugin
                ...
            
            def start(self):

                ... (generate or gather your data here) ...
                ... data = (use Structures to format your data for sending) ...
                self.plugin.push_data(data)
        
        self.__process = ExamplePluginSubprocess(self)
        self.__process.start()

```

Trafficking Events Through Subprocesses
=======================================

Similar to data generated by subprocesses, events can not be fired from subprocesses without some extra help, due to the
inter-process isolation.  

Again, similar to how data is trafficked to the core for subprocesses, there exists a [communication pipeline] [2] for pushing events to the 
event handler.

To be allowed direct access to the event pipe from your plugin, you must add `needs_event_pipe = True` to the superclass constructor
call at the top of your plugin. Here's an example:

```
class ExamplePlugin(Plugin):

    def __init__(self):

        Plugin.__init__(self, needs_dir = False, needs_comm_pipe = False, needs_event_pipe = True)
        
        ...

    def __start(self, *args):

        class ExamplePluginSubprocess(multiprocessing.Process):

            def __init__(self, plugin, *args):

                Process.__init__(self, name = "ExamplePluginSubprocess")
                
                self.plugin = plugin
                ...
            
            def start(self):

                ... (generate or gather your data here) ...
                ... data = (make sure your data is in the proper format for processing by the target event)
                self.plugin.push_event("EventName", data)
        
        self.__process = ExamplePluginSubprocess(self)
        self.__process.start()

```

Contributing
============

If you wish to contribute to this project, make sure your changes follow the following conventions:

1. Use spaces, not tabs.  Spaces are much prettier.
2. When indenting, only use four spaces per indention.
3. Use method_name, not methodName when naming methods/fields/etc.
4. When working with "private or protected" methods, use `__method__`, `_method_`, `_method`, or `__method`.
5. Make sure your code is readable enough that someone can determine what it does if you don't provide documentation with it.  If you provide docs, go crazy.

If you wish to contribute long-term to the project (eg., repo contributor..), send an email to <pirogoeth@maio.me> noting what you want to accomplish and tell me why you want to help :)

If this readme is lacking any crucial information, file an issue stating what is wrong and I'll get right to fixing it.

License
=======

```
ashiema: a lightweight, modular IRC bot written in python.
Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
```

   [1]: http://docs.python.org/2/library/multiprocessing.html                                           "Python 2.7.5 Documentation: multiprocessing"
   [2]: http://docs.python.org/2/library/multiprocessing.html#exchanging-objects-between-processes      "Python 2.7.5 Documentation: multiprocessing: Exchanging data between processes"
   [3]: http://docs.python.org/2/library/multiprocessing.html#multiprocessing.Pipe                      "Python 2.7.5 Documentation: multiprocesing.Pipe"