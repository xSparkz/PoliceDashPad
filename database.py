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

import sqlite3
from geolib import *
from common import *

MAX_DISTANCE = 1.00  # 1km (We should be able to find a node within 1km of our location)
DISTANCE_TO_EXPAND = 0.005  # Expand search box by 5 meters at a time. Small increments
DISTANCE_TO_START_SEARCH = 0.020  # Start our search box at 20 meters.


class Street():
    
    # Variables to store information about a street
    __SpeedIsKnown = False
    __IsOneWay = False
    __NumOfLanes = int
    __StreetName = None
    __MaxSpeed = int
    __TypeOfStreet = 'residental'

    def __init__(self, StreetName, IsOneWay=False, NumOfLanes=0, MaxSpeed=0, TypeOfStreet='residental'):

        # Setup street information
        self.__IsOneWay = IsOneWay
        self.__NumOfLanes = NumOfLanes
        self.__TypeOfStreet = TypeOfStreet
        self.__StreetName = StreetName

        if int(MaxSpeed) == 0: # Speed is not known, so lets take a guess:
            
            if TypeOfStreet == 'residential':

                self.__MaxSpeed = 50 # km / hr

            elif TypeOfStreet == 'tertiary': # 

                self.__MaxSpeed = 50 # km / hr

            elif TypeOfStreet == 'secondary': # Main street

                self.__MaxSpeed = 60 # km / hr

            elif TypeOfStreet == 'primary': # Highway

                self.__MaxSpeed = 80 # km / hr

            elif TypeOfStreet == 'motorway': # Major Highway

                self.__MaxSpeed = 100 # km / hr

            else:
                self.__MaxSpeed = 50 # km / hr # Not sure what kind of road it is, assume 50 km / hr

        else: # We do know the speed

            self.__SpeedIsKnown = True
            self.__MaxSpeed = MaxSpeed

    def SpeedIsKnown(self):

        return self.__SpeedIsKnown

    def StreetName(self):

        return self.__StreetName

    def MaxSpeed(self):

        return self.__MaxSpeed


class DataBase():
    
    def __init__(self):
        
        self.__Database = None # Database Object
        self.__Cursor = None # Cursor Object used to search databases


    def __del__(self): # Cleanup

        if not self.__Database is None:

            self.__Database.commit() # Commit the changes to the database
            self.__Database.close() # Close the database

    def Connect(self):

        self.__Database = sqlite3.connect(DATABASE_LOCATIONS, check_same_thread=False)  # Connect to database
        self.__Cursor = self.__Database.cursor()  # Get a cursor so we can work with our database


    def CommitChanges(self):

        self.__Database.commit()  # Commit changes to database


    def GetNodeCoordinates(self, osmid):

        Echo('Retrieving node coordinates for OSMID: ' + osmid)

        self.__Cursor.execute('''SELECT lat, lon FROM nodes WHERE osmid=?;''', (osmid,))

        Node = self.__Cursor.fetchone()

        if not Node is None:

            Echo('Node coordinates for:' + osmid + Node[0] + Node[1])
            return Node[0], Node[1]

        else:
            return None



    def IsIntersection(self, osmid):

        # Find out how many 'ways' the node belongs to. If the count is greater than 1 then it is an intersection.
        # If 1 is returned the function will report false because 1-1 is 0. Anything non zero is true.

        self.__Cursor.execute('''SELECT count(wayid) FROM way_nodes WHERE osmid=?;''', (osmid,))
        NodeCount = self.__Cursor.fetchone()

        return bool(int(NodeCount[0])-1)


    def FetchNearbyIntersections(self, osmid):
        # todo
        # print 'Fetching Street Names Connected to OSMID: ', osmid

        self.__Cursor.execute('''SELECT wayid, orderid FROM way_nodes WHERE osmid=?;''', (osmid,))

        Ways = self.__Cursor.fetchall()


        if not len(Ways) == 0:  # Did we find any ways that match our query?

            for Way in Ways:
                self.__Cursor.execute(
                    '''SELECT street_name, num_of_lanes, maxspeed, street_type, oneway FROM way_info WHERE wayid=?;''',
                    (Way[0],))

        else:

            # print 'Uh Oh! No Matching Streets Found Connected to OSMID: ', osmid
            return None


    def FetchStreets(self, osmid):

        # print 'Fetching Street Names Connected to OSMID: ', osmid

        self.__Cursor.execute('''SELECT wayid FROM way_nodes WHERE osmid=?;''', (osmid,))

        Ways = self.__Cursor.fetchall() # Find all the 'ways'

        Streets = [] # Create a new list to store the streets we found

        if not len(Ways) == 0:  # Did we find any ways that match our query?

            for Way in Ways:

                self.__Cursor.execute(
                    '''SELECT street_name, num_of_lanes, maxspeed, street_type, oneway FROM way_info WHERE wayid=?;''',
                    (Way[0],))

                WayInfo = self.__Cursor.fetchone()

                if not WayInfo is None:
                    Streets.append(Street(WayInfo[0], bool(WayInfo[4]), WayInfo[1], WayInfo[2], WayInfo[3]))

            # print 'Done! Finished Fetching Street Names.'
            return Streets

        else:

            # print 'Uh Oh! No Matching Streets Found Connected to OSMID: ', osmid
            return None


    def FindClosestNode(self, Coordinates):
        # Lets create a box around our location starting with a small box and expanding as necessary

        Distance = DISTANCE_TO_START_SEARCH  # Start our search within a 20 meter (default) box of our given location

        while Distance <= MAX_DISTANCE:

            # print '\nSeach Radius of: ', Distance, 'meters'
            SWCorner, NECorner = CreateBox(Distance, Coordinates)

            # print 'SELECT osmid FROM nodes WHERE lon>=' + str(SWCorner[1]) + ' AND lon<= ' + str(NECorner[1]) + \
            # ' AND lat>=' + str(SWCorner[0]) + ' AND lat<= ' + str(NECorner[0]) + ';'

            self.__Cursor.execute(
                '''SELECT osmid, lat, lon FROM nodes WHERE lon>=? AND lon <=? AND lat>=? AND lat <=?;''',
                (float(SWCorner[1]), float(NECorner[1]), float(SWCorner[0]), float(NECorner[0])))

            Nodes = self.__Cursor.fetchall()

            if not len(Nodes) == 0:  # Did we find any nodes that match our query?

                ShortestDistance = None  # Used to store the distance of the closest node and determine which one is in fact closest
                NodeOSMID = 0  # OSMID of node

                for Node in Nodes:

                    NodeDistance = DistanceBetween((Node[1], Node[2]), Coordinates)

                    if ShortestDistance is None:

                        ShortestDistance = NodeDistance
                        # NodeID = Node[0] # ID of found node
                        NodeOSMID = Node[0]

                    if NodeDistance < ShortestDistance:

                        ShortestDistance = NodeDistance
                        # NodeID = Node[0] # ID of found node with shortest distance
                        NodeOSMID = Node[0]

                        # print('{0}: {1}, {2}'.format(Node[0], Node[1], Node[2]))

                if not NodeOSMID == 0:

                    # print '\nNode with shortest distance: ', NodeID, '(', ShortestDistance, ') OSMID: ', NodeOSMID
                    return NodeOSMID  # We found our closest node, no need to search further

                else:

                    # print 'No matching nodes found.. Expanding search area..'
                    Distance += DISTANCE_TO_EXPAND  # Expand our box

            else:
                # print 'No matching nodes found.. Expanding search area..'
                Distance += DISTANCE_TO_EXPAND  # Expand our box

        return None  # We didn't find anything...


    def Close(self):
        self.__Database.close()