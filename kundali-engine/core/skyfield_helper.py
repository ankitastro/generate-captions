# In core/skyfield_helper.py

from skyfield.api import load, Topos

# Load the ephemeris and timescale data once.
# This might download a file on the first run.
eph = load('de421.bsp')
ts = load.timescale()

# Define the Sun and Earth
sun = eph['sun']
earth = eph['earth']

def get_observer(latitude, longitude):
    """Creates a Skyfield observer object for a given location."""
    return earth + Topos(latitude_degrees=latitude, longitude_degrees=longitude)