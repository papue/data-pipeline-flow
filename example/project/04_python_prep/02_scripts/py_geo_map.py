import geopandas as gpd
import folium

# Load processed geodata
districts = gpd.read_file("../03_output/py_districts_joined.geojson")

# Build interactive map
m = folium.Map(location=[51.5, 10.0], zoom_start=6)
folium.GeoJson(districts).add_to(m)

# Save map to HTML
MAP_OUT = "../03_output/py_districts_map.html"
m.save(MAP_OUT)
