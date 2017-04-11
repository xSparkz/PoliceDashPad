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

import math

MIN_LAT = math.radians(-90)
MAX_LAT = math.radians(90)
MIN_LON = math.radians(-180)
MAX_LON = math.radians(180)

EARTH_RADIUS = 6378.1  # Kilometers

def DistanceBetween(FirstCoordinates, SecondCoordinates):
    # Purpose: To determine the distance from one location to another
    # Usage: DistanceBetween((43.894655, -78.802791), (43.894245, -78.804540))
    # Coordinates are in (Lattitude, Longitude) format

    if not (len(FirstCoordinates) == 2) or not (len(SecondCoordinates) == 2):
        raise Exception('Improper Usage: - (LattitudeA, LongitudeA), (LattitudeB, LongitudeB)')

    # First Coordinate
    LattitudeA = math.radians(FirstCoordinates[0])
    LongitudeA = math.radians(FirstCoordinates[1])

    # Second Coordinate
    LattitudeB = math.radians(SecondCoordinates[0])
    LongitudeB = math.radians(SecondCoordinates[1])

    return EARTH_RADIUS * math.acos(
                math.sin(LattitudeA) *
                math.sin(LattitudeB) +
                math.cos(LattitudeA) *
                math.cos(LattitudeB) *
                math.cos(LongitudeA - LongitudeB))

def Direction(Bearing):
    # Purpose: To determine the direction of travel (ie. North) based on supplied bearing

    if Bearing <= 22.50:
        return "NB" # North Bound

    elif Bearing <= 67.50:
        return "NE" # North East

    elif Bearing <= 112.50:
        return "EB" # East Bound

    elif Bearing <= 157.50:
        return "SE" # South East

    elif Bearing <= 202.50:
        return "SB" # South Bound

    elif Bearing <= 247.50:
        return "SW" # South West

    elif Bearing <= 292.50:
        return "WB" # West Bound

    elif Bearing <= 337.50:
        return "NW" # North West

    else:
        return "NB" # North Bound

def BearingBetween(FirstCoordinates, SecondCoordinates):
    # Purpose: To determine the bearing in degrees from one location to another
    # Usage: Bearing((43.894655, -78.802791), (43.894245, -78.804540))
    # Coordinates are in (Lattitude, Longitude) format

    if not (len(FirstCoordinates) == 2) or not (len(SecondCoordinates) == 2):
        raise Exception('Improper Usage: - (LattitudeA, LongitudeA), (LattitudeB, LongitudeB)')

    # First Coordinate
    LattitudeA = math.radians(FirstCoordinates[0])
    LongitudeA = math.radians(FirstCoordinates[1])

    # Second Coordinate
    LattitudeB = math.radians(SecondCoordinates[0])
    LongitudeB = math.radians(SecondCoordinates[1])


    FormulaOne = LongitudeB - LongitudeA

    FormulaTwo = math.log(math.tan(LattitudeB/2.0+math.pi/4.0)/math.tan(LattitudeA/2.0+math.pi/4.0))

    if abs(FormulaOne) > math.pi:

         if FormulaOne > 0.0:

             FormulaOne = -(2.0 * math.pi - FormulaOne)

         else:

             FormulaOne = (2.0 * math.pi + FormulaOne)

    return (math.degrees(math.atan2(FormulaOne, FormulaTwo)) + 360.0) % 360.0


def CreateBox(Distance, Coordinates):
    # Purpose: To create a box around a location using the distance supplied. The box can then be used in a search to find
    # nearby coordinates that fall inside the box.
    # Usage: CreateBox(0.015, (43.894655, -78.802791))
    # distance is in meters
    # Coordinates are in (Lattitude, Longitude) format
    # Returns: the coordinates of the South West and North East corner of the box ex: ((43.894655, -78.802791), (43.894245, -78.804540))

    if not len(Coordinates) == 2:
        raise Exception('Improper Usage: - (LattitudeA, LongitudeA)')

    if Distance < 0:
        raise Exception("Illegal Argument - Distance cannot be less than 0")

    # Coordinates
    Lattitude = math.radians(float(Coordinates[0]))
    Longitude = math.radians(float(Coordinates[1]))

    # Angular distance in radians on a great circle
    Angular_Distance = Distance / EARTH_RADIUS

    MinimumLattitude = Lattitude - Angular_Distance
    MaximumLattitude = Lattitude + Angular_Distance

    if MinimumLattitude > MIN_LAT and MaximumLattitude < MAX_LAT:

        DeltaLongitude = math.asin(math.sin(Angular_Distance) / math.cos(Lattitude))

        MinimumLongitude = Longitude - DeltaLongitude

        if MinimumLongitude < MIN_LON:
            MinimumLongitude += 2 * math.pi

        MaximumLongitude = Longitude + DeltaLongitude

        if MaximumLongitude > MAX_LON:
            MaximumLongitude -= 2 * math.pi

    # A pole is within the Distance
    else:

        MinimumLattitude = max(MinimumLattitude, MIN_LAT)
        MaximumLattitude = min(MaximumLattitude, MAX_LAT)

        MinimumLongitude = MIN_LON
        MaximumLongitude = MAX_LON

    return [(math.degrees(MinimumLattitude), math.degrees(MinimumLongitude)),
        (math.degrees(MaximumLattitude), math.degrees(MaximumLongitude))]

def IsInSight(Bearing, FirstCoordinates, SecondCoordinates, FieldOfVisionDegrees=45):
    # Purpose: To determine if a GPS location is within sight of your location
    # given your current bearing (direction of travel) and Field of Vision
    # FieldOfVisionDegrees forms a cone from the Bearing provided and the function
    # tests to see if your destination coordinates fall inside that cone.
    # Usage: IsInSight(201.0, (43.894655, -78.802791), (43.894245, -78.804540), 45)
    # Returns: True or False

    LeftSide = Bearing - FieldOfVisionDegrees # Left side of the cone (originating from our bearing)
    Rightside = Bearing + FieldOfVisionDegrees # Right side of the cone (originating from our bearing)

    if LeftSide < 0: # Keep our value within the 360 degrees of our circle/compass
        LeftSide += 360 # ex: -15 + 360 = 345 degrees (End of the circle again) Moving left around the circle

    if Rightside > 360: # Keep our value within the 360 degrees of our circle/compass
        Rightside -= 360 # ex: 380 - 360 = 20 degrees (Start of the circle again) Moving right around the circle

    DestinationBearing = BearingBetween(FirstCoordinates, SecondCoordinates)

    if DestinationBearing < LeftSide or DestinationBearing > Rightside:
        return  False

    else:
        return True