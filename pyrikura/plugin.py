"""
*
*   copyright: 2012 Leif Theden <leif.theden@gmail.com>
*   license: GPL-3
*
*   This file is part of pyrikura/purikura.
*
*   pyrikura is free software: you can redistribute it and/or modify
*   it under the terms of the GNU General Public License as published by
*   the Free Software Foundation, either version 3 of the License, or
*   (at your option) any later version.
*
*   pyrikura is distributed in the hope that it will be useful,
*   but WITHOUT ANY WARRANTY; without even the implied warranty of
*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*   GNU General Public License for more details.
*
*   You should have received a copy of the GNU General Public License
*   along with pyrikura.  If not, see <http://www.gnu.org/licenses/>.
*
"""
from yapsy.PluginManager import PluginManager as IPluginManager
from yapsy.IPlugin import IPlugin

from types import StringType, ListType
import sys


class Plugin(IPlugin):
    """
    This is the interface for plugins

    The simple interface allows them to be managed by a shell.

    set/get
    set and get public variables

    cmd_XXX
    allow commands to be invoked from the shell

    """

    def __init__(self):
        self.is_activated = False

    @classmethod
    def new(cls, *arg, **kwarg):
        if not hasattr(cls, '_decendant'):
            raise Exception, 'class {} does not have decendant set'.format(
                cls.__name__)
        return cls._decendant(*arg, **kwarg)

    def setvar(self, name, value):
        if not hasattr(self, "public"):
            return False
        elif name in self.public:
            setattr(self, name, value)
            return True
        else:
            return False

    def getvar(self, name):
        if not hasattr(self, "public"):
            return None
        elif name in self.public:
            return str(getattr(self, name))
        else:
            return None

    def get_variables(self):
        def getter(v):
            return getattr(self, v)

        if not hasattr(self, "public"):
            return None
        else:
            d = {}
            d.update([(x[0], x[1]) for x in
                      zip(self.public, map(getter, self.public))])
            return d

    def check_requirements(self):
        if hasattr(self, "required") == False:
            return True

        missing = []
        not_activated = []
        ok = True

        if isinstance(self.required, StringType):
            req = [self.required]
        elif isinstance(self.required, ListType):
            req = self.required

        for plugin in req:
            l = [p.plugin_object for p in plugin_manager.getAllPlugins() if
                 p.name == plugin]
            if l == []:
                missing.append(plugin)
                continue

            for p in l:
                if p.is_activated == False:
                    not_activated.append(plugin)

        if missing != []:
            ok = False
            for plugin in missing:
                print
                "Cannot load %s.  Required plugin %s is not loaded." % \
                (self.__class__.__name__, plugin)

        if not_activated != []:
            ok = False
            for plugin in not_activated:
                print
                "Cannot load %s.  Required plugin %s is not activated." % \
                (self.__class__.__name__, plugin)

        return ok

    def activate(self):
        if self.check_requirements() == False:
            print
            "cannotload", self
            return

        if hasattr(self, "public"):
            if isinstance(self.public, StringType):
                self.public = [self.public]

            for v in self.public:
                setattr(self, v, None)

        if hasattr(self, "listen"):
            if isinstance(self.listen, StringType):
                self.listen = [self.listen]

            for t in self.listen:
                plugin_manager.register_listener(self, t)

        self.is_activated = True
        if hasattr(self, "OnActivate"):
            self.OnActivate()

    def deactivate(self):
        for t in self.listen:
            plugin_manager.unregister_listener(self, t)


class PluginManager(IPluginManager):
    def __init__(self, *args, **kwargs):
        kwargs["categories_filter"] = {'Default': Plugin}
        super(PluginManager, self).__init__(*args, **kwargs)
        self.listeners = {}
        self.resources = {}

    def register_type(self, t):
        self.listeners[t] = []

    def register_listener(self, plugin, t):
        try:
            self.listeners[t].append(plugin)
        except KeyError:
            print
            "Cannot set %s to listen for %s.  Data type is not known." % \
            (plugin, t)

    def unregister_listener(self, plugin, t):
        try:
            self.listeners[t].remove(plugin)
        except:
            pass

    def register_resource(self, name, value):
        if isinstance(name, StringType):
            self.resources[name] = value
        else:
            print
            "Cannot register resource %s: must be a string" % name

    def get_resources(self, *l):
        return [self.get_resource(i) for i in l]

    def get_resource(self, name):
        try:
            return self.resources[name]
        except KeyError:
            print
            "Cannot find resource: %s\n" % name

    def publish(self, t, *args, **kwargs):
        """
        Send this information to our listeners.
        """
        if len(self.listeners[t]) == 0:
            return args

        return [p.publish(*args, **kwargs) for p in self.listeners[t]]


plugin_manager = PluginManager()
