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

from imposm.parser import OSMParser
import sqlite3
import sys
import getopt
import os


class DataBase():

    def __init__(self):
        self.db = None
        self.cursor = None

    def Connect(self, Filename):
        self.db = sqlite3.connect(Filename) # Create database
        self.cursor = self.db.cursor() # Get a cursor so we can work with our database

    def DropTables(self):

        self.cursor.execute('''DROP TABLE IF EXISTS nodes''')
        self.cursor.execute('''DROP TABLE IF EXISTS way_nodes''')
        self.cursor.execute('''DROP TABLE IF EXISTS way_info''')

        self.db.commit() # Commit to changes made above

    def CreateTable(self):
        # CREATE TABLE STRUCTURES
        # Create our virtual R-Tree table used for spatial queries
        self.cursor.execute('''CREATE VIRTUAL TABLE nodes USING
        rtree(osmid INT PRIMARY KEY, lon REAL, lat REAL)''')

        # Table to store the OSMID where 'id' of the nodes_ids table corresponds to the 'id' of the nodes table
        # Used to identify a node by OSMID so we can retrieve supporting data stored in other tables
        self.cursor.execute('''CREATE TABLE way_nodes (id INT PRIMARY KEY, wayid INT, orderid INT, osmid INT)''')
        self.cursor.execute('''CREATE TABLE way_info (id INT PRIMARY KEY, wayid INT,
        street_name TEXT, num_of_lanes INT, maxspeed TEXT, street_type TEXT, oneway BOOLEAN)''')

        self.db.commit() # Commit to changes made above

    def AddWay(self, wayid, tags, refs):

        IsOneWay = False # Assume unless explicitly told otherwise
        MaxSpeed = 0 # A zero speed indicated the speed is unknown.

        if 'oneway' in tags:
            if tags['oneway'] == 'yes':
                IsOneWay = True

        if 'maxspeed' in tags:
            MaxSpeed = tags['maxspeed']

        if 'lanes' in tags:
            NumOfLanes = tags['lanes']

        else:
            NumOfLanes = 0 # Unknown

        if 'name' in tags:

            try:
                print 'Added Way: ', wayid
                print tags
                self.cursor.execute('''INSERT INTO way_info (wayid, street_name, num_of_lanes,
                maxspeed, street_type, oneway) VALUES(?,?,?,?,?,?)''', (wayid, tags['name'], NumOfLanes, MaxSpeed, tags['highway'], IsOneWay))

                OrderID = 0 # Start order of nodes in way at zero and store them in the database in order as well so they can be referenced later

                for ref in refs:
                    print '\t -', ref
                    self.cursor.execute('''INSERT INTO way_nodes(wayid, orderid, osmid) VALUES(?,?,?)''', (wayid, OrderID, ref))
                    OrderID += 1 # Increment order
                    # ADD NODE TO TREE

            except sqlite3.IntegrityError:
                print "Integrity Error"

    def CleanNodeTree(self):
        # Fastest slow method to remove nodes from database that aren't part of a 'way'
        # We are only concerned with nodes that form a street and if we don't remove the extra nodes
        # we need to check each node to see if it belongs to a way each and every time we find a node in the
        # database that is close to our location. This is slow and un-neccassary. By removing the extra nodes
        # we increase our lookup speed signifigantly.
        print 'Cleaning up un-used Nodes from Node Tree...'
        print 'This may take a while! Best grab a Coffee or a Beer. Or a Cranberry Juice?..'
        self.cursor.execute('''DELETE FROM nodes WHERE osmid NOT IN (SELECT osmid FROM way_nodes)''')
        print 'Cleanup Done!'


    def AddNode(self, osmid, lat, lon):
        print lat, lon # Debug info

        try:
            self.cursor.execute('''INSERT INTO nodes(osmid, lon, lat) VALUES(?,?,?)''', (int(osmid), float(lat), float(lon)))

        except sqlite3.IntegrityError:
            print "Integrity Error"

    def CommitChanges(self):
        self.db.commit() # Commit to changes


    def Close(self):
        self.db.close()


class __OSMData():

    def __init__(self):

        self.OSMDataBase = None
        self.__WayWhiteList = set(('motorway', 'trunk', 'primary', 'secondary',
                         'tertiary', 'unclassified', 'residential', 'service', 'road', 'motorway_link',
                         'trunk_link', 'primary_link', 'secondary_link', 'tertiary_link'))

    def SetDatabase(self, DataBase):

        self.OSMDataBase = DataBase


    def FoundNode(self, nodes):

        for osmid, lon, lat in nodes:
            # AddNode(self, lat, lon):
            # Purposely reversing the order of lat and lon in order to insert the correct values into the correct columns
            # in the SQLITE database. Reversing the order throws an exception that I have yet to debug. Some help?
            # This method currently serves it's purpose, but its confusing and messy.
            self.OSMDataBase.AddNode(osmid, lon, lat)

    def FoundWay(self, ways):

        for wayid, tags, refs in ways:
            if 'highway' in tags:
                if tags['highway'] in self.__WayWhiteList:
                    self.OSMDataBase.AddWay(wayid, tags, refs) # Found a street

def Import(InputFile, OutputFile):

    # Error checking
    if os.path.isfile(OutputFile):
        print 'Output file Already Exists:', OutputFile
        sys.exit(1)

    if not os.path.isfile(InputFile):
        print 'Input file Doesn\'t Exist:', InputFile
        sys.exit(1)

    if not __IsValidOsmFile(InputFile):
        print 'Input file does not appear to be a valid OSM (OpenStreetMap) formatted XML file.'
        sys.exit(1)

    if not __GetFileExtension(InputFile) == 'osm': # Check file extension
        # OSM Parser is finicky about the file extension
        print 'Input file has an unknown file extension.' \
              '\n' \
              'Input file should be a valid OSM (OpenStreetMap) formatted XML file. ie. Filename.osm. ' \
              '\n' \
              'File extension is case-sensitive.'
        sys.exit(1)

    # Setup OSM objects
    OSM = __OSMData() # Object used to process OSM data from XML file. Connected to ParseEngine via callbacks
    ParseEngine = OSMParser(concurrency=4, ways_callback=OSM.FoundWay, coords_callback=OSM.FoundNode) # XML Parser (set callback)

    # Create and connect database
    OSMDataBase = DataBase()
    OSMDataBase.Connect(OutputFile)
    OSMDataBase.DropTables()
    OSMDataBase.CreateTable()

    OSM.SetDatabase(OSMDataBase)

    # Parse OSM XML file
    ParseEngine.parse(InputFile)

    # Done - Cleanup
    OSMDataBase.CleanNodeTree() # Remove nodes that don't belong to a Way (ie. a Street)
    OSMDataBase.CommitChanges()
    OSMDataBase.Close()

    print OutputFile, 'successfully created..'
    print 'Finished!'
    sys.exit(0)


def Usage():

    print 'Uh oh! Improper usage! ' \
          '\n' \
          'Proper usage: osm-importer.py -i <inputfile> -o <outputfile>'


def __GetFileExtension(Filename):

    Extension = Filename.rsplit('.',1)

    if len(Extension) == 1:

        return None

    elif len(Extension) == 2:

        return Extension[1]


def __IsValidOsmFile(Filename):

    FileHandle = open(Filename)

    for LineNumber, LineContents in enumerate(FileHandle):

        if LineNumber == 1: # Line 2

            # Lets check the line for an OSM tag: ie. <osm version...
            if '<osm' in LineContents and 'version' in LineContents:
                FileHandle.close()
                return True

        elif LineNumber > 1:

            FileHandle.close()
            return False

def __Main(argv):

    InputFile = ''
    OutputFile = ''

    try:

        Options, Arguments = getopt.getopt(argv,"i:o:")

    except getopt.GetoptError:

        Usage()
        sys.exit(2)

    if not len(Options) == 2:

        Usage()
        sys.exit(2)

    for Option, Argument in Options:

        if Option == '-i':
            InputFile = Argument

        elif Option == '-o':
            OutputFile = Argument

    Import(InputFile, OutputFile)


if __name__ == "__main__":

    __Main(sys.argv[1:])
