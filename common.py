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

from datetime import datetime

# GPS Settings
GPS_PORT = 1337

# Time Date Settings
FORMAT_TIME = '%I:%M (%S) %p' # ex: 12:34 (04) PM
FORMAT_DATE = '%d %b %Y - %A' # ex: 13 Nov 2014 - Monday

# Database Settings
DATABASE_LOCATIONS = 'sqlite/geo.sqlite'

# Date / Time Functions
def TimeStamp(): return datetime.now().strftime(FORMAT_TIME)
def DateStamp(): return datetime.now().strftime(FORMAT_DATE)

def Echo(LineToEcho):

    print LineToEcho



