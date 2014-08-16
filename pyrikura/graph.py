from collections import defaultdict


class Graph(object):
    def __init__(self):
        self._d = defaultdict(list)

    def update(self, parent, children):
        self._d[parent] = children

    def search(self, start):
        p = dict()
        q = list()
        q.append(start)
        p[start] = None

        while q:
            n = q.pop()
            yield p[n], n
            for c in self._d[n]:
               p[c] = n
               q.append(c)
