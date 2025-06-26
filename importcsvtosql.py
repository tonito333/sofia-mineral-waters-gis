import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from sqlalchemy import create_engine

CSV_FOLDER = r"D:\ФМИ\РАГИС\polygon_points_sofia" 
GEOJSON_FOLDER = r"D:\ФМИ\РАГИС\Database"
DB_CONNECTION = {
    "host": "ep-rapid-queen-a2jj322k.eu-central-1.pg.koyeb.app",
    "port": "5432",
    "dbname": "ragis",
    "user": "azbozhidar",
    "password": "2MI3400524@Fmi2025!"
}
SCHEMA = "azbozhidar_work"

os.makedirs(GEOJSON_FOLDER, exist_ok=True)

from urllib.parse import quote_plus

password = quote_plus(DB_CONNECTION['password'])

engine = create_engine(
    f"postgresql://{DB_CONNECTION['user']}:{password}@{DB_CONNECTION['host']}:{DB_CONNECTION['port']}/{DB_CONNECTION['dbname']}"
)

for filename in os.listdir(CSV_FOLDER):
    if filename.endswith(".csv"):
        filepath = os.path.join(CSV_FOLDER, filename)
        df = pd.read_csv(filepath)

        polygons = []
        attributes = []

        for poly_id, group in df.groupby("polygon_id"):
            group_sorted = group.sort_values(by="point_order")
            coords = list(zip(group_sorted['y'], group_sorted['x']))

            if coords[0] != coords[-1]:
                coords.append(coords[0])

            polygon = Polygon(coords)
            polygons.append(polygon)

            attributes.append({"polygon_id": poly_id, "rayon": group_sorted["rayon"].iloc[0]})

        gdf = gpd.GeoDataFrame(attributes, geometry=polygons, crs="EPSG:7801")

        geojson_path = os.path.join(GEOJSON_FOLDER, filename.replace(".csv", ".geojson"))

        if os.path.exists(geojson_path):
            os.remove(geojson_path)
        
        gdf.to_file(geojson_path, driver="GeoJSON")

        table_name = filename.replace(".csv", "").lower()
        gdf.to_postgis(table_name, con=engine, schema=SCHEMA, if_exists='replace', index=False)
        print(f"Обработено: {filename} → {table_name} в PostGIS")