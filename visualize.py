import folium
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import BytesIO
import geopandas as gpd

def get_country_centroids(countries_geojson):
    gdf = gpd.read_file(countries_geojson)
    gdf["centroid"] = gdf.geometry.centroid
    gdf = gdf.set_geometry("centroid")
    country_centroids = {
        row["admin"]: [row["centroid"].y, row["centroid"].x] for _, row in gdf.iterrows()
    }
    return country_centroids


def plot_earthquake_trend(country_data):
    if len(country_data) < 2:
        return None

    country_data['year'] = pd.to_datetime(country_data['time']).dt.year
    yearly_counts = country_data.groupby('year').size().reset_index(name='count')

    plt.figure(figsize=(6, 4))
    sns.lineplot(data=yearly_counts, x='year', y='count', marker='o', markersize=8, linewidth=2.5, color='blue', markerfacecolor='red', markeredgecolor='red')
    plt.xlabel('Year')
    plt.ylabel('Earthquakes')
    plt.title(f"Earthquake Trend for {country_data['country'].iloc[0]}")
    plt.grid(True)

    min_year, max_year = yearly_counts['year'].min(), yearly_counts['year'].max()
    plt.xticks(range(min_year, max_year + 1, max(1, (max_year - min_year) // 8)), rotation=45)

    min_count, max_count = yearly_counts['count'].min(), yearly_counts['count'].max()
    plt.yticks(range(min_count, max_count + 1, max(1, (max_count - min_count) // 5)))

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    return img_base64


from branca.element import MacroElement
from jinja2 import Template

class LegendControl(MacroElement):
    def __init__(self):
        super().__init__()
        self._name = 'LegendControl'

    def render(self, **kwargs):
        legend_html = '''
        <div style="
            position: fixed; 
            bottom: 50px; 
            left: 50px; 
            width: 150px; 
            height: 120px; 
            background-color: white; 
            border: 2px solid black; 
            z-index: 9999; 
            font-size: 14px;
            padding: 10px;
        ">
            <b>Earthquake Magnitude:</b><br>
            <i class="fa fa-circle" style="color:green"></i> 0-2<br>
            <i class="fa fa-circle" style="color:yellow"></i> 2-4<br>
            <i class="fa fa-circle" style="color:orange"></i> 4-6<br>
            <i class="fa fa-circle" style="color:red"></i> > 6<br>
            <b>Circle Size:</b><br>
            Proportional to magnitude
        </div>
        '''
        macro = MacroElement()
        macro._template = Template(legend_html)
        self.add_child(macro)

from folium.plugins import FloatImage

def add_legend(map_object):
    legend_url = "https://i.imgur.com/NRoaggQ.png" 
    legend = FloatImage(legend_url, bottom=5, left=5)
    map_object.add_child(legend)


def visualize_earthquakes_on_map(earthquakes_with_countries, countries_geojson):
    m = folium.Map()

    countries_layer = folium.FeatureGroup(name='Countries')
    folium.GeoJson(countries_geojson).add_to(countries_layer)

    earthquakes_layer = folium.FeatureGroup(name='Earthquakes')

    for _, row in earthquakes_with_countries.iterrows():
        mag_color = (
            "green" if row["magnitude"] <= 2 else
            "yellow" if row["magnitude"] <= 4 else
            "orange" if row["magnitude"] <= 6 else
            "red"
        )

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=row["magnitude"] * 1.5,
            color=mag_color,
            fill=True,
            fill_color=mag_color,
            fill_opacity=0.7,
            weight=1,
            tooltip=f"{row['place']} ({row['time']}) - Mag: {row['magnitude']}"
        ).add_to(earthquakes_layer)

    add_legend(m)
    m.add_child(countries_layer)
    m.add_child(earthquakes_layer)
    folium.LayerControl().add_to(m)

    country_centroids = get_country_centroids(countries_geojson)
    earthquakes_by_country = earthquakes_with_countries.groupby('country')

    for country, country_data in earthquakes_by_country:
        if not country_data.empty and country in country_centroids:
            img_base64 = plot_earthquake_trend(country_data)

            if img_base64:
                popup_html = f'<img src="data:image/png;base64,{img_base64}" alt="Earthquake Trend">'
            else:
                popup_html = "<p>No sufficient data available for this country.</p>"

            folium.Marker(
                country_centroids[country],
                popup=folium.Popup(html=popup_html, max_width=800),
                tooltip=country
            ).add_to(m)

    bounds = earthquakes_with_countries[['latitude', 'longitude']].values.tolist()
    m.fit_bounds(bounds)

    return m


if __name__ == "__main__":
    earthquakes_with_countries = pd.read_csv("earthquakes_with_countries.csv", low_memory=False)
    countries_geojson = "custom.geojson"

    map_with_earthquakes = visualize_earthquakes_on_map(earthquakes_with_countries, countries_geojson)
    # map_with_earthquakes.save("visualization4.html")
    
    html = map_with_earthquakes.get_root().render()

    with open("visualization.html", "w") as f:
        f.write('<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css">')
        f.write(html)

