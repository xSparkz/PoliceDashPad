__author__ = 'Steve Hollaway'

# This file is part of Police Dash Pad.

# Police Dash Pad is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Police Dash Pad is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Police Dash Pad.  If not, see <http://www.gnu.org/licenses/>.

from gpsmodule import GpsModule
from eventmanager import EventHandler

class MainApp():

    def __init__(self):

        # Initiate our GPS device and start receiving data
        self.GPS = GpsModule() # Setup GPS device
        self.GPS.start() # Start a new thread and execute GPS.run()

if __name__ == '__main__':

    DashPad = MainApp() # Main application
