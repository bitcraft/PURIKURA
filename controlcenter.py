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
"""
Touch/Mouse Control Panel for the kiosk.  Used by the operator only.

Require Kivy.
"""


"""
All settings used for the watcher and processor are set/listed here
"""

parser = argparse.ArgumentParser()
parser.add_argument('event',
                     help='name of event being managed',
                     type=str)


parser.add_argument("--iphoto", 
                    help='specify to import photos directly into
                    iphoto', 
                    action='store_true',
                    default=False)


parser.add_argument('--prints',
                    help='number of prints to be made',
                    type=int,
                    default=0)


parser.add_argument('--keep',
                    help='keep print images',
                    action='store_true',
                    default=False)


parser.add_argument('--incoming',
                    help='folder where new photos are placed'
                    type=str)


settings = parser.parse_args()

