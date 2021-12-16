#%%
import pandas as pd
import geopandas as gpd
import contextily as cx
import matplotlib.pyplot as plt
import folium
import webbrowser


#%%
gazetteerpath = "data/geonames/allCountries_cleaned.csv"
df = pd.read_csv(
    gazetteerpath,
    delimiter=","
)

#%%
filter_df = df[df["name"] == "Ade"]
filter_gdf = gpd.GeoDataFrame(filter_df,
                              geometry=gpd.points_from_xy(filter_df.longitude, filter_df.latitude),
                              crs={'init': 'epsg:4326'})

#%%
gpd.GeoSeries.explore(filter_gdf,
                      tiles="Stamen Watercolor",
                      marker_type='circle_marker',
                      marker_kwds={'radius': 100}).save("data/html/mapa.html")



#%%
ax = filter_gdf.plot()
ax.set_xlim(-0, 90)
ax.set_ylim(0, 90)
cx.add_basemap(ax,
               crs={'init': 'epsg:4326'},
               source=cx.providers.Stamen.Watercolor)
plt.show()




