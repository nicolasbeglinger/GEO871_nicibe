# %% [markdown]
# ## Import modules

# %%
import random
import inspect
import re
import os
import math


import pandas as pd
import geopandas as gpd
import folium
from folium import plugins
import nltk


import html2text


# %% [markdown]
# ## Minor Functions

# %% [markdown]
# Define function to debug

# %%
def prinfo(*args, **kwargs) -> None:
    """Prints arguments in with the name beforehand:
    example:
    x = 5
    print(x)

    #prints "x = 5"
    """

    frame = inspect.currentframe().f_back
    all_input = inspect.getframeinfo(frame).code_context[0]
    filtered_input = re.search(r"\((.*)\)", all_input).group(1)
    split_input = filtered_input.split(", ")

    if 'newline' in kwargs:
        newlinestring = "\n" if kwargs['newline'] else ""
    else:
        newlinestring = ""

    for var, val in zip(split_input, args):
        print(f"{var} = {newlinestring}{val}")

# %% [markdown]
# Define function to give information about the progress of reading the csv

# %%


def read_csv_in_chunks(path: str, n_lines: int, name_col: str, **read_params) -> pd.DataFrame:
    """Simmilar to pd.read_csv, but in chunks that enable to see the progress

    Returns:
        [pandas.DataFrame]: [description]
    """

    if 'chunksize' not in read_params or read_params['chunksize'] < 1:
        read_params['chunksize'] = 80000

    chunks = [0] * math.ceil(n_lines / read_params['chunksize'])

    for chunk_idx, chunk in enumerate(pd.read_csv(path, **read_params)):
        percent = min(
            ((chunk_idx + 1) * read_params['chunksize'] / n_lines) * 100, 100.0)
        print("#" * int(percent), f"{percent:.2f}%", end='\r', flush=True)
        chunks[chunk_idx] = chunk[chunk[name_col].notnull()]

    print()
    print("Now concatenating chunks...")
    data_frame = pd.concat(chunks, axis=0)
    del chunks
    print("Finished!")
    return data_frame

# %% [markdown]
# ## Import Stuff

# %% [markdown]
# ### Gazetteer

# %%


def read_gazetteer(gaz: str = 'nga') -> dict:
    """Reads in a gazetteer and returns it as dataframe in a property dictionary
    Args:
        gaz (str): ["nga", "geonames", "countries"]

    Returns:
        dict: {'df_gazetteer', 'idx_of_lat', 'idx_of_lon', 'nameCol'}
    """

    if gaz == "nga":
        gazetteerpath = "data/gazetteers/nga/countries_administrative.csv"
        # indexOfLat = 4
        # indexOfLon = 5
        idx_of_lat = 1
        idx_of_lon = 2
        n_lines = 484618  # for nga administrative
        # n_lines =  284485 #for nga administrative approved
        # n_lines = 7866485 #for nga administrative populated
        name_col = "SORT_NAME_RO"  # for nga

        # read in the gazetter csv
        gazetteer = read_csv_in_chunks(
            path=gazetteerpath,
            n_lines=n_lines,
            low_memory=False,
            name_col=name_col)

        gazetteer = pd.concat(
            [gazetteer,
             pd.read_csv("data/gazetteers/own_places.csv")]
        )

    elif gaz == "geonames":
        gazetteerpath = "data/geonames/allCountries_cleaned.csv"
        idx_of_lat = 2
        idx_of_lon = 3
        n_lines = 6974472  # for allCountries_cleaned.csv
        # n_lines = 2079830 # for allCountries_AT.csv
        name_col = "name"

        # read in the gazetter csv
        gazetteer = read_csv_in_chunks(
            path=gazetteerpath,
            n_lines=n_lines,
            low_memory=False,
            name_col=name_col)

    # Read gazetter data (csv) and save placenames in a list
    elif gaz == "countries":
        countrynames = pd.read_csv(
            "data/geodict_github/countrynames.csv", names=["short", "long"])
        countrypositions = pd.read_csv(
            "data/geodict_github/countrypositions.csv", names=["short", "lat", "lon"])

        gazetteer = countrynames.merge(countrypositions, on="short")
        gazetteer.long = gazetteer.long.str.strip()
        idx_of_lat = 2
        idx_of_lon = 3
        n_lines = 240
        name_col = "long"

    prop_dic = {
        'df_gazetteer': gazetteer,
        'idx_of_lat': idx_of_lat,
        'idx_of_lon': idx_of_lon,
        'nameCol': name_col
    }

    return prop_dic

# %% [markdown]
# ### Textfile

# %% [markdown]
# Import textfile or call the html2text function to extract the text from a given url \
# and save it for next use

# %%


def read_textfile(textfile: str = None, url: str = None) -> str:
    """Reads a textfile or extracts text from a website using html2text
    Args:
        textfile (str): path to textfile
        url (str): url of website

    Raises:
        Warning: If no path is specified

    Returns:
        str: loaded text or extracted text from website
    """

    if textfile:
        with open(textfile, "r", encoding="utf8") as raw_text:
            text_str = raw_text.read()

    elif url:
        text_save_path = f"data/texts/autosave/lastText_{url[-20:]}"

        if not os.path.exists(text_save_path):
            text_str = html2text.html2text(url=url)

            with open(text_save_path, "w", encoding="utf8") as raw_text:
                raw_text.write(text_str)

        else:
            with open(text_save_path, "r", encoding="utf8") as raw_text:
                text_str = raw_text.read()

    else:
        raise Warning("No path specified")

    return text_str


# url = 'https://www.theguardian.com/global-development/2021/dec/21/uk-accused-of-abandoning-\
# worlds-poor-as-aid-turned-into-colonial-investment'
# url = "https://www.theguardian.com/world/2021/oct/21/cuts-to-overseas-aid-thwart-uk-efforts-\
# to-fight-covid-pandemic"

# %% [markdown]
# ## Matching

# %% [markdown]
# Extract places from text using nltk

# %%
def create_placenames(text_str: str, gazetteer: pd.DataFrame, prop_dic: dict) -> tuple:
    """Extract placenames out of a text and return georeferenced results in a geodataframe and dict
    Args:
        text_str (str): text that placenames should get extracted from
        gazetteer (pandas.Dataframe) gazetteer
        prop_dic (dict): Dictionary with keys /
            {'df_gazetteer', 'idx_of_lat', 'idx_of_lon', 'nameCol'}

    Returns:
        [type]: [description]
    """

    tokenized = nltk.word_tokenize(text_str)
    tree = nltk.ne_chunk(nltk.pos_tag(tokenized))

    i = 0
    for word in tokenized:
        if word == "Asia":
            i += 1

    place_words = [
        " ".join(i[0] for i in t)
        for t in tree
        if hasattr(t, "label") and t.label() == "GPE"
    ]

    stemmer = nltk.stem.PorterStemmer()
    lemmatizer = nltk.stem.WordNetLemmatizer()
    place_words = [lemmatizer.lemmatize(word).upper().replace(
        " ", "") for word in place_words]
    # prinfo(sorted(places)[:10])
    print()

    # Create Dictionary with placenames as keys and dictionaries with the counts as values.
    place_dic = {}

    for place_word in place_words:
        if place_word in place_dic:
            place_dic[place_word]["count"] += 1
        else:
            place_dic[place_word] = {"count": 1}

    # Fill the dictionary with the coordinates of the placenames.

    # add column with lemmatized placenames two compare them to lematized placenames of the text
    gazetteer["lemma_placenames"] = gazetteer[prop_dic['nameCol']].apply(
        lemmatizer.lemmatize)
    gazetteer["stem_placenames"] = gazetteer[prop_dic['nameCol']].apply(
        stemmer.stem)

    len_keys = len(place_dic)
    log_interval = 1  # int(round(lenKeys/20, 0))

    failed_places = []

    for i, (placename, place_attributes) in enumerate(place_dic.items()):
        try:
            tmp_df_values = gazetteer.query(
                "lemma_placenames == @placename").values[0]
            # tmp_df_values = df_gazetteer[df_gazetteer["SORT_NAME_RO"] == "MAFIKENG"].values[0]
            place_attributes["name"] = tmp_df_values[7]
            place_attributes["lat"] = tmp_df_values[prop_dic['idx_of_lat']]
            place_attributes["lon"] = tmp_df_values[prop_dic['idx_of_lon']]

        except IndexError:
            failed_places.append(placename)

        # give feedback to progress
        if (i % log_interval == 0 and i > 0) or i+1 == len_keys:
            print(f"{i+1} of {len_keys} ({round((i/len_keys)*100, 1)}%)", end='\r')

    for i, (place_word, place_attributes) in enumerate(place_dic.items()):
        if i < 10:
            print((place_word, place_attributes))

    # Catch information about nonfound placenames and delete them from the dictionary
    num_fails = len(failed_places)
    for fail in failed_places:
        del place_dic[fail]

    print(f'{num_fails} words/places haven\'t been found in the gazetteer')

    data_frame = pd.DataFrame(
        [list(attributes.values()) + [place]
         for place, attributes in place_dic.items()],
        columns=["count", "name", "lat", "lon", "stemname"])

    geo = gpd.GeoDataFrame(
        data_frame,
        geometry=gpd.points_from_xy(data_frame.lon, data_frame.lat),
        crs=4326
    )

    return (geo, place_dic)

    # geojsonname = textfile[textfile.find("/")+1:textfile.find(".")][6:]
    # geo.to_file(f"data/geodataframes/{geojsonname}.geojson", driver='GeoJSON')

# %% [markdown]
# ## Initialization


# %%
dic = read_gazetteer()
df_gazetteer = dic['df_gazetteer']
text = read_textfile(
    url="https://www.theguardian.com/global-development/2022/jan/14/worlds-poorest-bear-brunt-of-\
        climate-crisis-10-underreported-emergencies")
# text = read_textfile("data/texts/tagesanzeiger_spendensammler.txt")
# text = read_textfile("data/texts/aid_wiki.txt")
places, d = create_placenames(
    text_str=text, gazetteer=df_gazetteer, prop_dic=dic)

# %% [markdown]
# ## Visualization

# %%
random.seed(1)

color_dic = {}
for i in range(places["count"].max()):
    color_dic[i+1] = f"#{random.randint(0, 0xFFFFFF)}"
color_dic = {
    1: '#440154',
    2: '#3b528b',
    3: '#21918c',
    4: '#5ec962',
    5: '#fde725'
}
print(color_dic)

color_list = [color_dic[count] for count in places["count"]]

# %%
# create map
heatMap = folium.Figure(width='75%')
heatMap = folium.Map(
    location=[15, 30],
    zoom_start=2,
    max_bounds=True,
    tiles=None).add_to(heatMap)

# add tiles
folium.TileLayer(tiles='Cartodb dark_matter', name="Dark").add_to(heatMap)
folium.TileLayer(tiles='stamen watercolor', name="Watercolor").add_to(heatMap)

# add points and markercluster
points = folium.FeatureGroup(name="Points", show=True).add_to(heatMap)
cluster = plugins.MarkerCluster(
    name="Cluster", show=False).add_to(heatMap)

for place, attributes in d.items():

    coordinates = (attributes['lat'], attributes['lon'])

    html = f'''

    <strong>Name:</strong> &emsp;&emsp;&emsp;&emsp;&emsp;{attributes['name']}<br/>
    <strong>Stemmed Name:</strong>&emsp;{place}<br/>
    <strong>Count:</strong>&emsp;&emsp;&emsp;&emsp;&emsp;{attributes['count']}
    
    '''

    iframe = folium.IFrame(
        html,
        width=300,
        height=70)

    popup = folium.Popup(iframe)

    folium.Circle(coordinates).add_to(cluster)
    folium.Circle(
        location=coordinates,
        popup=popup,
        tooltip=attributes['name'],
        radius=attributes['count'] * 50000,
        fill=True,
        color=color_dic[attributes['count']]
    ).add_to(points)


# extract coordinate of geodataframe
coordinates = [[point.xy[1][0], point.xy[0][0]] for point in places.geometry]

# add heatmap
plugins.HeatMap(
    name='HeatMap',
    data=coordinates,
    min_opacity=0.3,
    show=False
).add_to(heatMap)


new = []
for place in places.iterrows():
    for i in range(place[1]['count']):
        new.append(place[1])

geo_multiple = pd.DataFrame(new)

geo_multiple = gpd.GeoDataFrame(
    geo_multiple,
    geometry=gpd.points_from_xy(geo_multiple.lon, geo_multiple.lat),
    crs=4326
)

# extract coordinate of geodataframe
coordinates = [[point.xy[1][0], point.xy[0][0]]
               for point in geo_multiple.geometry]

# add heatmap
plugins.HeatMap(
    name='HeatMap_multiple',
    data=coordinates,
    min_opacity=0.3,
    show=False
).add_to(heatMap)

# add layercontrol
folium.LayerControl(collapsed=False).add_to(heatMap)


heatMap

# %%
pointMap = folium.Figure(width='35%')
gpd.GeoSeries.explore(
    places,
    color=color_list,
    max_bounds=True,
    tiles="Open Street Map",  # "Stamen Watercolor",
    marker_type='circle',
    marker_kwds={
        'radius': 50000,
        'fill': True}).add_to(pointMap)

# folium.TileLayer(tiles='stamen watercolor', name="Watercolor").add_to(pointMap)

pointMap

# %%
