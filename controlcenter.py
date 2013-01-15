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

