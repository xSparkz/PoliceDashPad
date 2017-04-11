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

from gpsmodule import *
from database import *
from PyQt4.QtCore import QObject, pyqtSignal

class EventHandler(QObject):

    def __init__(self):

        self.__Busy = False  # Are we doing something and need to wait?
        
        # Initiate our GPS device and start receiving data
        self.GPSDevice = GpsModule()  # Setup GPS device
        self.GPSDevice.start()  # Start a new thread and execute GPS.run()
        
        # Initialize Datase
        self.__Database = DataBase()  # Pointer to our Database.
        self.__Database.Connect()

        self.__Location_ClosestNodeID = None # Store the node id of the node closest to our current gps coordinates
        self.__Location_LastKnownNodeID = None # Store the node id of the last known node that is NOT an intersection
        # ^ used to determine what road your travelling on when you encounter an intersection since an intersection will report
        # more than one road. The last known node id that was not an intersection node will only belong to the road you were travelling on
        # so you can assume that if it doesnt belong to the other roads reported back, then those roads are your cross streets and can be
        # treated as such.

        # Slots - Connect signals to slots
        self.GPSDevice.signalLatitudeChanged.connect(self.__GetLocation) # Get the location if the lattitude changes
        
    def __del__(self):

        # Clean Up
        self.GPSDevice.Close() # Clean up
        self.GPSDevice = None # Clean up


    def __GetLocation(self):

        if not self.__Busy == True:

            self.__Busy = True # Don't run another location search until we're finished with the current search

            self.__Location_ClosestNodeID = self.__Database.FindClosestNode((self.__Gps.Lattitude(), self.__Gps.Longitude()))

            if self.__Location_ClosestNodeID == self.__Location_LastKnownNodeID:
                # Our last known location is the same as our closest ID so theres no point running a database check to
                # find out what street we are on, because we already know. Only run a check when our ClosestNodeID and our
                # LastKnownNodeID don't match. (ie. we've moved)

                self.__Busy = False # Done checks (No longer busy)
                return # No need to check any further, we know where we are

            if not self.__Database.IsIntersection(self.__Location_ClosestNodeID): # Our current location is NOT an intersection

                self.__Location_LastKnownNodeID = self.__Location_ClosestNodeID # Keep track of the last known node thats not an intersection

                Streets = self.__Database.FetchStreets(self.__Location_ClosestNodeID) # Check database for list of streets connected to the node we're close to

                if not Streets is None:

                    for Street in Streets:
                        self.__Gui.CurrentLocation(Street.StreetName())
                        self.__Gui.MaxSpeed(Street.MaxSpeed(), Street.SpeedIsKnown())

                self.__Busy = False  # Done checks (No longer busy)

            else:
                pass
                # todo
                # We are at or close to an intersection so we need to do some figuring out to determine which street we are actually
                # travelling on and which streets intersect.

                # 1. Check each street, 2. If our last known node is a part of that street then that is the street we are currently on
                # 2. Or don't do a street check. (Remain on last known road until known otherwise)

            return
