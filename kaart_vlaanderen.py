import csv
import json

paths_geo = [r"C:\Users\annab\Documents\P&O 3", r"C:\Users\jarne\Desktop\KUL 2Bir - Semester 3\P&O3"]
paths_web = [r"C:\Users\annab\Documents\P&O 3", r"C:\Users\jarne\PycharmProjects\KUL Bir - 2e semester\P&O3" ]
i = 0
# 0 = Annabel
# 1 = Jarne

vlaanderen_arrondisementen_path = paths_geo[i] + r"\vlaanderen_arrondisement\Refarr25G10.shp"
vlaanderen_gemeenten_path = paths_geo[i] + r"\vlaanderen_gemeentes\Refgem25G100.shp"
gemeenten_riscios_path = paths_geo[i] + r"\gemeenten_risicos.csv"
arrondisement_risicos_path = paths_geo[i] + r"\arrondisement_risicos_test2.csv"
kaart_html_path = paths_web[i] + r"\website_flask\static/kaarten/kaart_vlaanderen.html"
csv_bestand = paths_web[i] + r"\website_flask\static/data/straatnamen_per_gemeente_raar.csv"

# Pad naar de kaart
kaart_html_path = r'static/kaarten/kaart_vlaanderen.html'

# kaart_vlaanderen.py
import folium
import numpy as np
from folium.plugins import HeatMapWithTime, HeatMap
import os
import pysteps
from datetime import datetime
from HDF_lezer import data_lezer

rand = [[51.800, 1.13000], [50.244, 7.250]] #deze buiten functie want ook nodig voor heatmap
def init_map(vlaanderen_gemeenten):
    # Maak een Folium-kaart (folium.map(centrumlocatie, hoeveelheid zoom, kaartstijl))
    m = folium.Map(location=[51.0458, 4.326962], 
                   zoom_start=8.3, min_zoom = 8.30, #min_zoom kan niet verder uitzoomen
                   tiles="cartodb positron",
                   control_scale=True,) # schaal vanonder aan kaart
    
    # Gemeentes toevoegen
    for _, row in vlaanderen_gemeenten.iterrows():
        geojson_geometry = row['geometry'].__geo_interface__
        folium.GeoJson(
            geojson_geometry,
            style_function=lambda x,control=False: {
                'color': 'black', 'weight': 1, 'opacity':1,
            },
            popup=folium.Popup(f"Gemeente: {row['NAAM']}", max_width=300),
        ).add_to(m)
    m.fit_bounds(rand)
    m.options['maxBounds'] = rand # dit zorgt ervoor dat je niet buiten de rand kan pannen => !!!! zorgt wel ervoor dat kaart raar laadt (of iets anders want als dit er niet is nog steeds robleem)
    return m

def add_gemeenten_layer(m, vlaanderen_gemeenten, vervaging = 1, gemeenten_risicos=0):

    # Kolom verwijderen (zodat er geen meerdere kolommem risico zijn):
    vlaanderen_gemeenten = vlaanderen_gemeenten.drop(columns=['RISICO'], errors='ignore')
    # Kolom met huidige risicos toevoegen:
    vlaanderen_gemeenten = vlaanderen_gemeenten.merge(gemeenten_risicos, on='NAAM', how='left')

    # Nieuwe kolom toevoegen met juiste kleur per gemeente: 
            # iterrows: gaat door alle rijen van dataframe => geeft tuple met index en dan hele rij (Pandas)
            # met row['RISICO']: neem je de kolom van risico uit de rij
    for _, row in vlaanderen_gemeenten.iterrows():
        color = 'rgb(78, 146, 72)' #groen
        if row['RISICO'] > 2000:
            color = 'rgb(210, 50, 47)' #rood
        elif row['RISICO'] > 1000:
            color = 'rgb(222, 104, 55)' #oranje


        # Gemeentes toevoegen
        geojson_geometry = row['geometry'].__geo_interface__
        folium.GeoJson(
            geojson_geometry,
            style_function=lambda x,control=False,color=color: {
                'color': 'black', 'weight': 1, 'fillColor': color, 'opacity':vervaging,'fillOpacity': vervaging
            },
            popup=folium.Popup(f"Gemeente: {row['NAAM']}<br>Risico: {row['RISICO']}", max_width=300),
        ).add_to(m)
    return m


def highlight_selected_gemeente(m, vlaanderen_gemeenten, geselecteerde_gemeente):
    for _, row in vlaanderen_gemeenten.iterrows():
        color = 'rgb(78, 146, 72)' #groen
        if row['NAAM'] == geselecteerde_gemeente:
            color = 'rgb(19, 57, 128)'
        elif row['RISICO'] > 2000:
            color = 'rgb(210, 50, 47)' #rood
        elif row['RISICO'] > 1000:
            color = 'rgb(222, 104, 55)' #oranje
    

        # Gemeentes toevoegen
        geojson_geometry = row['geometry'].__geo_interface__
        folium.GeoJson(
            geojson_geometry,
            style_function=lambda x, color=color: {
                'color': 'black', 'weight': 1, 'fillColor': color, 'fillOpacity': 1
            },
            popup=folium.Popup(f"Gemeente: {row['NAAM']}<br>Risico: {row['RISICO']}", max_width=300),
        ).add_to(m)
    return m

def data_extracting_rainfall(data_path):
    #Locatie van mapje
    hdf_filepath = data_path
    hdf_files = os.listdir(hdf_filepath)

    # Create empty arrays for precipitation and timestamps
    precipitation = []
    timestamps = []

    # Read hdf file with pysteps for all files in path
    agg_type = "ACRR"  # Or 'RATE', 'DBZH' depending on your data type
    """
    "ACRR" voor geaccumuleerde neerslag --> deze voor gegevens van KMI
    "RATE" voor regenvalintensiteit
    "DBZH" voor radarreflectiviteit
    """
    for hdf_file in hdf_files:
        hdf_datetime = hdf_file.split('.')[0]
        hdf_timestamp = datetime.strptime(hdf_datetime, '%Y%m%d%H%M%S')
        [hdf_precipitation, _, metadata
         ] = pysteps.io.importers.import_odim_hdf5(f'{hdf_filepath}/{hdf_file}',qty=agg_type.upper())
        precipitation = np.append(precipitation, hdf_precipitation)
        timestamps = np.append(timestamps, hdf_timestamp)

    # Reshape qpe array
    n_timesteps = len(hdf_files)
    gridsize = 700
    precipitation = precipitation.reshape((n_timesteps, gridsize,gridsize))
    precipitation = np.nan_to_num(precipitation,nan=0.0)

    return precipitation

def add_rainfall_layer_h(m,data_path): 
    print("Extracting data from HDF-file")
    precipitation = data_lezer(data_path,False)
    print("Data extracted")
    print("Creating default map and coordinates")
    # Initialiseer de basiskaart
    min_lat, max_lat = 47.4, 53.7
    min_lon, max_lon = -0.26669, 9.7
    gridsize = 700

    # Stel een standaard lat/lon bereik
    lat_range = np.linspace(min_lat, max_lat, gridsize)
    lon_range = np.linspace(min_lon, max_lon, gridsize)
    print("Default map created")
    print("Converting data")
    # Maak de data per tijdstap
    data = []
    a = 24
    for t in range(a):
        timestep_data = []
        print(f"Current timestamp: {t}")
        for i in range(gridsize):
            for j in range(gridsize):
                lat = float(lat_range[i])
                lon = float(lon_range[j])
                intensity = float(precipitation[t, i, j])
                if intensity != 0.0 and rand[1][0] < lat < rand[0][0] and rand[0][1]< lon < rand[1][1]: #overmatige gegevens wissen
                    timestep_data.append([lat, lon, intensity])
        data.append(timestep_data)
    print("Data converted")
    # Genereer de tijdindex voor de heatmap
    time_index = [f"{data_path[66:74]} 2022 van {k}:00 tot {k + 1}:00 uur." for k in range(a)]
    print("Printing data")
    # Voeg de heatmap met tijd toe aan de kaart
    HeatMapWithTime(data,index=time_index,auto_play=True,max_opacity=1,radius=5, name="Uurlijke neerslag").add_to(m)
    #HeatMap(data_vast, radius=5, max_zoom=1, name="Dagelijkse neerslag").add_to(m) #kan nog gradient toevoegen
    print("Data printed")
    return m

def add_rainfall_layer_d(m,data_path):
    print("Extracting data from HDF-file")
    regen_data = data_lezer(data_path,True)
    print("Data extracted")
    print("Making default map and coordinates")
    # Initialiseer de basiskaart
    min_lat, max_lat = 47.4, 53.7
    min_lon, max_lon = -0.26669, 9.7
    gridsize = 700

    # Stel een standaard lat/lon bereik
    lat_range = np.linspace(min_lat, max_lat, gridsize)
    lon_range = np.linspace(min_lon, max_lon, gridsize)
    print("Default map made")
    print("Converting data")
    # Maak de data per tijdstap
    data = []
    for i in range(gridsize):
        for j in range(gridsize):
            lat = float(lat_range[i])
            lon = float(lon_range[j])
            intensity = float(regen_data[i, j])
            if intensity != 0.0 and rand[1][0] < lat < rand[0][0] and rand[0][1]< lon < rand[1][1]:
                data.append([lat, lon, intensity])

    print("Data converted")
    print("Printing data")
    # Voeg de heatmap met tijd toe aan de kaart
    # heatmap_layer = folium.FeatureGroup(name="Regendata Heatmap")
    HeatMap(data, radius=10, blur=15, max_zoom=1).add_to(m)  # kan nog gradient toevoegen
    # heatmap_layer.add_to(m)
    print("Data printed")
    return m

def clean_text(text):
    corrections = {
        "\\u00e9": "é",  # é
        "\\u00e8": "è",  # è
        "\\u00ea": "ê",  # ê
        "\\u00eb": "ë",  # ë
        "\\u00e0": "à",  # à
        "\\u00f4": "ô",  # ô
        "\\u00e7": "ç",  # ç
        # Voeg hier meer ongewenste tekens toe indien nodig
    }
    for unicode_escape, correct_char in corrections.items():
        text = text.replace(unicode_escape, correct_char)
    return text

def straten_per_gemeente():
    straten_per_gemeente = {}

    with open(csv_bestand, mode="r") as csv_file:
        reader = csv.DictReader(csv_file)
        veldnamen = reader.fieldnames

        for row in reader:
            gemeente_naam = row[veldnamen[0]]

            straten = json.loads(row[veldnamen[1]])
            straten2 = []
            for straat in sorted(straten):
                straten2.append(clean_text(straat))
            straten_per_gemeente[gemeente_naam] = straten2
        print('lijst gemaakt 1')
    return straten_per_gemeente


