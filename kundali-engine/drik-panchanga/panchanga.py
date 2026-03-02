from __future__ import division
from math import floor, ceil
from collections import namedtuple as struct
import swisseph as swe
import math

Date = struct('Date', ['year', 'month', 'day'])
Place = struct('Location', ['latitude', 'longitude', 'timezone'])

# Convert 23d 30' 30" to 23.508333 degrees
from_dms = lambda degs, mins, secs: degs + mins/60 + secs/3600

# the inverse
def to_dms(deg):
  try:
    if not isinstance(deg, (int, float)) or math.isnan(deg) or math.isinf(deg):
      return [0, 0, 0]
    d = int(deg)
    mins = (deg - d) * 60
    m = int(mins)
    s = int(round((mins - m) * 60))
    return [d, m, s]
  except (ValueError, TypeError):
    return [0, 0, 0]

def unwrap_angles(angles):
  """Add 360 to those elements in the input list so that all elements are sorted in ascending order."""
  result = angles[:]
  for i in range(1, len(angles)):
    if result[i] < result[i-1]: result[i] += 360
  assert(result == sorted(result))
  return result

def inverse_lagrange(x, y, ya):
  """Given two lists x and y, find the value of x = xa when y = ya, i.e., f(xa) = ya"""
  assert(len(x) == len(y))
  total = 0
  for i in range(len(x)):
    numer = 1
    denom = 1
    for j in range(len(x)):
      if j != i:
        numer *= (ya - y[j])
        denom *= (y[i] - y[j])
    total += numer * x[i] / denom
  return total

gregorian_to_jd = lambda date: swe.julday(date.year, date.month, date.day, 0.0)
jd_to_gregorian = lambda jd: swe.revjul(jd, swe.GREG_CAL)

def solar_longitude(jd):
  try:
    data = swe.calc_ut(jd, swe.SUN)
    return data[0][0]
  except Exception:
    return 0.0

def lunar_longitude(jd):
  try:
    data = swe.calc_ut(jd, swe.MOON)
    return data[0][0]
  except Exception:
    return 0.0

def lunar_latitude(jd):
  try:
    data = swe.calc_ut(jd, swe.MOON)
    return data[0][1]
  except Exception:
    return 0.0

def sunrise(jd, place):
  try:
    lat, lon, tz = place
    result = swe.rise_trans(jd - tz/24, swe.SUN, lon, lat, rsmi=swe.BIT_DISC_CENTER + swe.CALC_RISE)
    rise = result[1][0]
    return [rise + tz/24., to_dms((rise - jd) * 24 + tz)]
  except Exception:
    return [jd, [6, 0, 0]]

def sunset(jd, place):
  try:
    lat, lon, tz = place
    result = swe.rise_trans(jd - tz/24, swe.SUN, lon, lat, rsmi=swe.BIT_DISC_CENTER + swe.CALC_SET)
    setting = result[1][0]
    return [setting + tz/24., to_dms((setting - jd) * 24 + tz)]
  except Exception:
    return [jd, [18, 0, 0]]

def moonrise(jd, place):
  try:
    lat, lon, tz = place
    result = swe.rise_trans(jd - tz/24, swe.MOON, lon, lat, rsmi=swe.BIT_DISC_CENTER + swe.CALC_RISE)
    rise = result[1][0]
    return to_dms((rise - jd) * 24 + tz)
  except Exception:
    return [0, 0, 0]

def moonset(jd, place):
  try:
    lat, lon, tz = place
    result = swe.rise_trans(jd - tz/24, swe.MOON, lon, lat, rsmi=swe.BIT_DISC_CENTER + swe.CALC_SET)
    setting = result[1][0]
    return to_dms((setting - jd) * 24 + tz)
  except Exception:
    return [0, 0, 0]

def tithi(jd, place):
    try:
        # Use exact JD for birth time instead of sunrise
        moon_phase = lunar_phase(jd)
        if math.isnan(moon_phase) or math.isinf(moon_phase):
            print(f"tithi: Invalid moon_phase={moon_phase} for jd={jd}, place={place}")
            return [1, [0, 0, 0]]
        today = int(ceil(moon_phase / 12))
        if today < 1 or today > 30:
            print(f"tithi: Invalid tithi number={today} for jd={jd}, place={place}")
            today = 1
        # Return tithi with zero end time for compatibility
        answer = [today, to_dms(0)]
        print(f"tithi: Success, result={answer} for jd={jd}, place={place}")
        return answer
    except Exception as e:
        print(f"tithi: Exception occurred: {e} for jd={jd}, place={place}")
        return [1, [0, 0, 0]]
    
def nakshatra(jd, place):
  try:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    # Use exact JD instead of sunrise - matches kundali_engine calculation
    moon_longitude = lunar_longitude(jd)
    ayanamsa = swe.get_ayanamsa_ut(jd)
    # If ayanamsa is a tuple, extract the first element
    if isinstance(ayanamsa, tuple):
      ayanamsa = ayanamsa[0]
    sidereal_longitude = (moon_longitude - ayanamsa) % 360

    # Calculate nakshatra (1-27) - same formula as kundali_engine
    nak = int(sidereal_longitude * 27 / 360) + 1
    if nak < 1 or nak > 27:
      nak = 1

    # Return nakshatra with zero end time for compatibility
    return [nak, to_dms(0)]
  except Exception:
    return [1, [0, 0, 0]]

def yoga(jd, place):
  try:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    lat, lon, tz = place
    rise = sunrise(jd, place)[0] - tz / 24
    lunar_long = (lunar_longitude(rise) - swe.get_ayanamsa_ut(rise)) % 360
    solar_long = (solar_longitude(rise) - swe.get_ayanamsa_ut(rise)) % 360
    total = (lunar_long + solar_long) % 360
    yog = int(ceil(total * 27 / 360))  # Explicitly convert to int
    if yog < 1 or yog > 27:
      yog = 1
    degrees_left = yog * (360 / 27) - total
    offsets = [0.25, 0.5, 0.75, 1.0]
    lunar_long_diff = [(lunar_longitude(rise + t) - lunar_longitude(rise)) % 360 for t in offsets]
    solar_long_diff = [(solar_longitude(rise + t) - solar_longitude(rise)) % 360 for t in offsets]
    total_motion = [moon + sun for (moon, sun) in zip(lunar_long_diff, solar_long_diff)]
    y = total_motion
    x = offsets
    approx_end = inverse_lagrange(x, y, degrees_left)
    ends = (rise + approx_end - jd) * 24 + tz
    answer = [yog, to_dms(ends)]
    lunar_long_tmrw = (lunar_longitude(rise + 1) - swe.get_ayanamsa_ut(rise + 1)) % 360
    solar_long_tmrw = (solar_longitude(rise + 1) - swe.get_ayanamsa_ut(rise + 1)) % 360
    total_tmrw = (lunar_long_tmrw + solar_long_tmrw) % 360
    tomorrow = int(ceil(total_tmrw * 27 / 360))  # Explicitly convert to int
    isSkipped = (tomorrow - yog) % 27 > 1
    if isSkipped:
      leap_yog = yog + 1
      degrees_left = leap_yog * (360 / 27) - total
      approx_end = inverse_lagrange(x, y, degrees_left)
      ends = (rise + approx_end - jd) * 24 + tz
      answer += [leap_yog, to_dms(ends)]
    return answer
  except Exception:
    return [1, [0, 0, 0]]

def karana(jd, place):
  try:
    rise = sunrise(jd, place)[0]
    solar_long = solar_longitude(rise)
    lunar_long = lunar_longitude(rise)
    moon_phase = (lunar_long - solar_long) % 360
    today = int(ceil(moon_phase / 6))  # Explicitly convert to int
    if today < 1 or today > 60:
      today = 1
    degrees_left = today * 6 - moon_phase
    return [today]
  except Exception:
    return [1]

def vaara(jd):
  try:
    return int(ceil(jd + 1) % 7)  # Explicitly convert to int
  except Exception:
    return 0

def masa(jd, place):
  try:
    ti = tithi(jd, place)[0]
    critical = sunrise(jd, place)[0]
    last_new_moon = new_moon(critical, ti, -1)
    next_new_moon = new_moon(critical, ti, +1)
    this_solar_month = raasi(last_new_moon)
    next_solar_month = raasi(next_new_moon)
    is_leap_month = (this_solar_month == next_solar_month)
    maasa = int(this_solar_month + 1)  # Explicitly convert to int
    if maasa > 12:
      maasa = (maasa % 12)
    if maasa < 1:
      maasa = 1
    return [maasa, is_leap_month]
  except Exception:
    return [1, False]

ahargana = lambda jd: jd - 588465.5

def elapsed_year(jd, maasa_num):
  try:
    sidereal_year = 365.25636
    ahar = ahargana(jd)
    kali = int((ahar + (4 - maasa_num) * 30) / sidereal_year)
    saka = kali - 3179
    vikrama = saka + 135
    return kali, saka
  except Exception:
    return 0, 0

def new_moon(jd, tithi_, opt=-1):
  try:
    if opt == -1:
      start = jd - tithi_
    if opt == +1:
      start = jd + (30 - tithi_)
    x = [-2 + offset/4 for offset in range(17)]
    y = [lunar_phase(start + i) for i in x]
    y = unwrap_angles(y)
    y0 = inverse_lagrange(x, y, 360)
    return start + y0
  except Exception:
    return jd

def raasi(jd):
  try:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    solar_nirayana = (solar_longitude(jd) - swe.get_ayanamsa_ut(jd)) % 360
    return int(ceil(solar_nirayana / 30.))  # Explicitly convert to int
  except Exception:
    return 1

def lunar_phase(jd):
  try:
    solar_long = solar_longitude(jd)
    lunar_long = lunar_longitude(jd)
    moon_phase = (lunar_long - solar_long) % 360
    return moon_phase
  except Exception:
    return 0.0

def samvatsara(jd, maasa_num):
  try:
    kali = elapsed_year(jd, maasa_num)[0]
    if kali >= 4009:
      kali = (kali - 14) % 60
    samvat = (kali + 27 + int((kali * 211 - 108) / 18000)) % 60
    return samvat
  except Exception:
    return 0

def ritu(masa_num):
  try:
    return (masa_num - 1) // 2
  except Exception:
    return 0

def day_duration(jd, place):
  try:
    srise = sunrise(jd, place)[0]
    sset = sunset(jd, place)[0]
    diff = (sset - srise) * 24
    return [diff, to_dms(diff)]
  except Exception:
    return [12, [12, 0, 0]]

# ----- TESTS ------
def all_tests():
  print(moonrise(date2, bangalore))
  print(moonset(date2, bangalore))
  print(sunrise(date2, bangalore)[1])
  print(sunset(date2, bangalore)[1])
  assert(vaara(date2) == 5)
  print(sunrise(date4, shillong)[1])
  assert(karana(date2, helsinki) == [14])
  return

def tithi_tests():
  feb3 = gregorian_to_jd(Date(2013, 2, 3))
  apr24 = gregorian_to_jd(Date(2010, 4, 24))
  apr19 = gregorian_to_jd(Date(2013, 4, 19))
  apr20 = gregorian_to_jd(Date(2013, 4, 20))
  apr21 = gregorian_to_jd(Date(2013, 4, 21))
  print(tithi(date1, bangalore))
  print(tithi(date2, bangalore))
  print(tithi(date3, bangalore))
  print(tithi(date2, helsinki))
  print(tithi(apr24, bangalore))
  print(tithi(feb3, bangalore))
  print(tithi(apr19, helsinki))
  print(tithi(apr20, helsinki))
  print(tithi(apr21, helsinki))
  return

def nakshatra_tests():
  print(nakshatra(date1, bangalore))
  print(nakshatra(date2, bangalore))
  print(nakshatra(date3, bangalore))
  print(nakshatra(date4, shillong))
  return

def yoga_tests():
  may22 = gregorian_to_jd(Date(2013, 5, 22))
  print(yoga(date3, bangalore))
  print(yoga(date2, bangalore))
  print(yoga(may22, helsinki))

def masa_tests():
  jd = gregorian_to_jd(Date(2013, 2, 10))
  aug17 = gregorian_to_jd(Date(2012, 8, 17))
  aug18 = gregorian_to_jd(Date(2012, 8, 18))
  sep19 = gregorian_to_jd(Date(2012, 9, 18))
  may20 = gregorian_to_jd(Date(2012, 5, 20))
  may21 = gregorian_to_jd(Date(2012, 5, 21))
  print(masa(jd, bangalore))
  print(masa(aug17, bangalore))
  print(masa(aug18, bangalore))
  print(masa(sep19, bangalore))
  print(masa(may20, helsinki))
  print(masa(may21, helsinki))

if __name__ == "__main__":
  bangalore = Place(12.972, 77.594, +5.5)
  shillong = Place(25.569, 91.883, +5.5)
  helsinki = Place(60.17, 24.935, +2.0)
  date1 = gregorian_to_jd(Date(2009, 7, 15))
  date2 = gregorian_to_jd(Date(2013, 1, 18))
  date3 = gregorian_to_jd(Date(1985, 6, 9))
  date4 = gregorian_to_jd(Date(2009, 6, 21))
  apr_8 = gregorian_to_jd(Date(2010, 4, 8))
  apr_10 = gregorian_to_jd(Date(2010, 4, 10))
  masa_tests()