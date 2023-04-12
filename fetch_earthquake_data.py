import requests
import pandas as pd

import time

def fetch_earthquake_data_page(start_time, end_time, min_magnitude, limit, offset):
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={start_time}&endtime={end_time}&minmagnitude={min_magnitude}&limit={limit}&offset={offset}"
    
    max_retries = 5
    retry_delay = 5  # seconds

    for attempt in range(max_retries):
        response = requests.get(url)
        if response.status_code == 200:
            try:
                data = response.json()
                break
            except ValueError:
                pass
        else:
            print(f"Request failed with status code {response.status_code}. Retrying...")
        
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
    else:
        print(f"Failed to fetch data after {max_retries} attempts. Returning an empty DataFrame.")
        return pd.DataFrame()

    earthquakes = []
    for feature in data["features"]:
        earthquakes.append({
            "time": pd.to_datetime(feature["properties"]["time"], unit="ms"),
            "latitude": feature["geometry"]["coordinates"][1],
            "longitude": feature["geometry"]["coordinates"][0],
            "magnitude": feature["properties"]["mag"],
            "place": feature["properties"]["place"]
        })

    return pd.DataFrame(earthquakes)


def fetch_earthquake_data(start_time, end_time, min_magnitude):
    limit = 20000  # Maximum number of events per request
    offset = 1
    all_earthquakes = pd.DataFrame()

    while True:
        earthquakes = fetch_earthquake_data_page(start_time, end_time, min_magnitude, limit, offset)
        if earthquakes.empty:
            break
        all_earthquakes = pd.concat([all_earthquakes, earthquakes], ignore_index=True)
        offset += limit

    return all_earthquakes


start_time = "2000-01-01"
end_time = "2022-12-31"
min_magnitude = 4.5

earthquake_data = fetch_earthquake_data(start_time, end_time, min_magnitude)
earthquake_data.to_csv("earthquake_data.csv", index=False)
