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

import gps
import threading
import os
from common import *
from geolib import *
from time import sleep
from PyQt4.QtCore import QObject, pyqtSignal # Used to emit signals

GPS_STATUS = {'nostatus': 0, 'nofix': 1, '2d': 2, '3d': 3}

class GpsModule(threading.Thread, QObject):

    # Signals
    signalSpeedChanged = pyqtSignal(int)
    signalBearingChanged = pyqtSignal()
    signalLatitudeChanged = pyqtSignal()
    signalLongitudeChanged = pyqtSignal()

    def __init__(self):

        # Initialize GPS device
        if not os.path.exists('/dev/ttyUSB0'): # Check to see if USB GPS device is connected
            raise Exception('GPS Device not connected!')

        # GPS Services
        os.system('sudo killall gpsd') # Shutdown gps daemon
        sleep(0.5) # Give our above command time to work

        os.system(str('sudo gpsd /dev/ttyUSB0 -F /var/run/gpsd.sock -S ' + GPS_PORT)) # Start gps daemon (spits out GPS data from device to USB port)
        sleep(1) # Wait a second for gps daemon to initialize before trying to work with it

        # Initialize Threading (So we can do stuff while we're doing stuff)
        threading.Thread.__init__(self) # Open a new thread
        self.daemon = True # Set as a daemon thread to run in background


        # GPS Information
        self.__Latitude = int # Lattitude
        self.__Longitude = int # Longitutde
        self.__Speed = int # Speed in km
        self.__Bearing = float # Bearing/Direction of travel in degrees
        self.__Status = int # Store the status of our GPS device (0 no status, 1 no fix, 2 2d mode, 3, 3d mode)

        # Initiate GPS session
        self.__GPSDevice = gps.gps("localhost", GPS_PORT)
        self.__GPSDevice.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
        self.__Polling = False # If set to true then continually check the GPS for incomming data

    def Status(self):
        # Used with GPS_STATUS
        # (0) No information
        # (1) No fix
        # (2) 2d mode (lattitude & longittude) visible
        # (3) 3d mode (lattitude, longittude, and altittude) visible
        return self.__Status

    def Speed(self): # How fast are we travelling?
        return self.__Speed

    def Bearing(self): # Whats our bearing?
        return self.__Bearing

    def Direction(self): # Whats our direction of travel?
        return Direction(self.__Bearing)

    def Longitude(self): # GPS Longitude
        return self.__Longitude

    def Lattitude(self): # GPS Latitude
        return self.__Latitude

    def Time(self): # What time is it based on the sattelite?
        return self.__GPSDevice.utc

    # Function Over-ride - Called when thread is started
    def run(self):

        while self.__Polling: # Continually check for new GPS information (poll)

            try: # Allow us to catch errors if something unexpected happens

                Report = self.__GPSDevice.next() # Grab report from GPS device

                if Report['class'] == 'TPV':

                    if hasattr(Report, 'mode'):

                        self.__Status = Report.mode

                    if hasattr(Report, 'track'):

                        self.__Bearing = Report.track
                        self.signalBearingChanged.emit() # Emit signal

                    if hasattr(Report, 'speed'):

                        self.__Speed = int(round(Report.speed * gps.MPS_TO_KPH)) # Convert speed to kilometers; round to the nearest number; then drop the decimal

                        # Sometimes the GPS reports a speed of 1 or 2 when not in motion.
                        # So if the speed is equal to or less than 2 then just report 0 as our speed
                        # We are most likely not moving nor are we interested in speeds that low
                        if self.__Speed <= 2: self.__Speed = 0  # Set speed to zero

                        self.signalSpeedChanged.emit(self.__Speed) # Emit signal

                    if hasattr(Report, 'lat'):

                        self.__Latitude = Report.lat
                        self.signalLatitudeChanged.emit() # Emit signal

                    if hasattr(Report, 'lon'):

                        self.__Longitude = Report.lon
                        self.signalLongitudeChanged.emit() # Emit signal

            except KeyError:
                pass # Ignore

            except KeyboardInterrupt:
                quit()

            except StopIteration:
                self.__GPSDevice = None
                Echo('GPS Dameon has stopped')

    def Close(self):

        # Clean up
        self.__Polling = False # Stop polling
        os.system('sudo killall gpsd')  # Shutdown gps daemon