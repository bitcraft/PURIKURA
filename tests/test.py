#!/usr/bin/env python
"""
This program is the nuts and bolts of the photo booth.
"""
import sys
import os

# CHANGE THIS
head = '/Volumes/Mac2/Users/leif/pycharm/PURIKURA'

sys.path.append(head)
sys.path.append(os.path.join(head, 'pyrikura/'))

from twisted.internet import reactor, defer
from twisted.plugin import getPlugins
import logging

from pyrikura import ipyrikura
from pyrikura.graph import Graph
from pyrikura.config import Config


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("purikura.test")


def get_class(o):
    name = o.__class__.__name__
    if name.endswith('Factory'):
        name = name[:-7]
    return "%s (%s)" % (name, id(o))


class Session:
    def __init__(self):
        logger.debug('building new session...')

        p = dict((get_class(p).split(" ")[0], p) for p in
                 getPlugins(ipyrikura.IPyrikuraPlugin))

        for name in p.keys():
            logger.debug("loaded plugin %s", name)

        pi0 = p['AddString'].new('001')
        pi1 = p['AddString'].new('002')
        pi2 = p['AddString'].new('003')
        pi3 = p['PassThrough'].new()

        g = Graph()
        g.update(pi0, [pi1, pi2])
        g.update(pi1, [pi3])
        self.graph = g
        self.head = pi0

    def start(self, result=None):

        # start processing chain
        chain = self.graph.search(self.head)

        r = dict()
        def log(result, plugin, parent=None):
            if parent:
                print "---->\t%s\t%s\t%s" % \
                (get_class(parent), get_class(plugin), result)
            else:
                print "====>\t%s\t%s" % (get_class(plugin), result)
            return result

        print "setting up"
        # build callback chain
        dd = dict()
        parent, head_plugin = next(chain)
        head_deferred = defer.Deferred()
        head_deferred.addCallback(head_plugin.process)
        dd[head_plugin] = head_deferred
        print "    >", None, get_class(head_plugin)

        def err(fail):
            #print "error!"
            print fail

        for parent, plugin in chain:
            print "    >", get_class(parent), get_class(plugin)

            d = defer.Deferred()
            d.addCallback(log, plugin, parent)
            d.addCallbacks(plugin.process, err)
            dd[plugin] = d

            #dd[parent].addCallback(d.callback)
            #d.chainDeferred(dd[parent])
            dd[parent].chainDeferred(d)

        print
        print "     \tparent\t\t\tplugin\t  \t\tlast result"
        # start the callbacks
        head_deferred.callback('capture.jpg')


if __name__ == '__main__':
    session = Session()
    reactor.callWhenRunning(session.start)
    try:
        reactor.run()
    except:
        reactor.stop()
        raise
