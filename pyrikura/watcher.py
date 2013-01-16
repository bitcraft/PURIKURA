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

import os



class Watcher(pubsub):
    """
    Simple watcher that uses a glob to track new files
    This class will publish paths to new images
    """

    def __init__(self, path, filter=None):
        super(self, Watcher).__init__()
        self._path = path
        self._filter = filter
        self.reset()

    def reset(self):
        self._seen = set()

    def tick(self, td=0.0):
        if self._filter is None:
            files = set(os.listdir(self._path))

        # get files that have not been seen before and publish them
        self.publish(files - self._seen)

        # add the new items to the seen set
        self._seen.update(files)
