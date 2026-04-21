library(sf)
library(tmap)

# Read shapefile of study regions
regions <- st_read("../01_input/r_study_regions.shp")

# Read GeoJSON of points of interest
poi <- st_read("../01_input/r_poi.geojson")

# Spatial join
joined <- st_join(regions, poi)

# Write result as GeoPackage
st_write(joined, "../03_output/r_regions_joined.gpkg", delete_dsn = TRUE)

# Write result as shapefile
st_write(joined, "../03_output/r_regions_joined.shp", delete_dsn = TRUE)

# Save map to PNG
map <- tm_shape(joined) + tm_polygons("category")
tmap_save(map, "../03_output/r_region_map.png", width = 1800, height = 1200)
