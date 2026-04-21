import geopandas as gpd

# Read shapefile from raw input
districts = gpd.read_file("../01_input/py_districts.shp")

# Read GeoPackage
admin_bounds = gpd.read_file("C:/data/gis/admin_boundaries.gpkg", layer="level2")

# Spatial join
merged = gpd.sjoin(districts, admin_bounds, how="left", predicate="intersects")

# Write shapefile output
merged.to_file("../03_output/py_districts_joined.shp")

# Write GeoJSON
merged.to_file("../03_output/py_districts_joined.geojson", driver="GeoJSON")
