"""
Download NASA FIRMS yearly country files (MODIS and VIIRS S-NPP).

Run on your own laptop:  python download.py
Files land in ./data/<sensor>/<year>/...csv

Country file names follow the FIRMS archive pattern:
  https://firms.modaps.eosdis.nasa.gov/data/country/modis/2020/modis_2020_Nepal.csv
If a country gives 404, open https://firms.modaps.eosdis.nasa.gov/country/
and check the exact spelling FIRMS uses, then edit COUNTRIES below.
"""
import os
import sys
import urllib.request

BASE = "https://firms.modaps.eosdis.nasa.gov/data/country"
SENSORS = ["modis", "viirs-snpp"]
YEARS = range(2013, 2025)  # overlap period: both sensors flying
COUNTRIES = ["United_States", "Nepal", "Bangladesh", "Egypt", "Australia", "India", "Brazil"]

# Start small: pass country names on the command line to fetch only those,
# e.g.  python download.py Nepal United_States
if len(sys.argv) > 1:
    COUNTRIES = sys.argv[1:]

failed = []
for sensor in SENSORS:
    for year in YEARS:
        for country in COUNTRIES:
            name = f"{sensor}_{year}_{country}.csv"
            url = f"{BASE}/{sensor}/{year}/{name}"
            out = os.path.join("data", sensor, str(year), name)
            if os.path.exists(out) and os.path.getsize(out) > 0:
                continue
            os.makedirs(os.path.dirname(out), exist_ok=True)
            try:
                print("get", url)
                urllib.request.urlretrieve(url, out)
            except Exception as e:
                print("  FAILED:", e)
                failed.append(url)
                if os.path.exists(out):
                    os.remove(out)

print(f"\nDone. {len(failed)} failed.")
for u in failed:
    print("  ", u)
