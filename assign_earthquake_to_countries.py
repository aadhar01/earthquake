import geopandas as gpd
import pandas as pd

def assign_earthquakes_to_countries(earthquake_data, countries_geojson):
    gdf = gpd.read_file(countries_geojson)
    earthquakes = gpd.GeoDataFrame(earthquake_data, geometry=gpd.points_from_xy(earthquake_data.longitude, earthquake_data.latitude))
    earthquakes.crs = gdf.crs

    earthquakes_with_countries = gpd.sjoin(earthquakes, gdf, op="within", how="inner")
    earthquakes_with_countries = earthquakes_with_countries.drop(columns=["index_right", "geometry"])
    earthquakes_with_countries = earthquakes_with_countries.rename(columns={"name": "country"})

    return earthquakes_with_countries

earthquake_data = pd.read_csv("earthquake_data.csv")
countries_geojson = "custom.geojson"

earthquakes_with_countries = assign_earthquakes_to_countries(earthquake_data, countries_geojson)
earthquakes_with_countries.to_csv("earthquakes_with_countries.csv", index=False)
