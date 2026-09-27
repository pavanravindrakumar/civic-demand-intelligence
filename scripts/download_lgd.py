import urllib.request
import os

os.makedirs('data/raw', exist_ok=True)

print("Downloading LGD Villages data...")
url = "https://raw.githubusercontent.com/planemad/india-local-government-directory/master/data/villages.csv"
try:
    urllib.request.urlretrieve(url, "data/raw/lgd_villages.csv")
    print("Successfully downloaded LGD villages data.")
except Exception as e:
    print(f"Failed to download LGD villages: {e}")

print("Downloading LGD Districts data...")
url_districts = "https://raw.githubusercontent.com/planemad/india-local-government-directory/master/data/districts.csv"
try:
    urllib.request.urlretrieve(url_districts, "data/raw/lgd_districts.csv")
    print("Successfully downloaded LGD districts data.")
except Exception as e:
    print(f"Failed to download LGD districts: {e}")
