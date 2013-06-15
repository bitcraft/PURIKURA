class Node(object):
    def __init__(self, plugin_name, *arg, **kwarg):
        self.plugin_name = plugin_name
        self._listening = []
        self._err_listening = []
        self._arg = arg
        self._kwarg = kwarg

    def load(self, pm):
        plugin = pm.getPluginByName(self.plugin_name)
        if not plugin:
            raise ValueError, "cannot load plugin {}".format(self.plugin_name)
        broker = plugin.plugin_object.new(*self._arg, **self._kwarg)
        return broker

    def subscribe(self, other):
        self._listening.append(other)

    def subscribe_error(self, other):
        self._err_listening.append(other)

    def get_children(self):
        open_list = [self]
        children = []
        while open_list:
            parent = open_list.pop()
            children = parent._children[:]
            while children:
                child = children.pop()
                open_list.append(child)
                yield child
