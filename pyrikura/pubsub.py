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

class pubsub(object):

    def __init__(self, path, filter=None):
        self._subscribers = []

    def __enter__(self):
        pass

    def __exit__(self):
        pass

    def process(self, msg):
        pass

    def subscribe(self, other):
        other._subscribers.append(self)

    def publish(self, iterable):
        for msg in iterable:
            for sub in self._subscribers:
                sub.process(msg, sender=self)

