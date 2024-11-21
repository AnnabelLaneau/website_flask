import folium
import csv
import json
import random
from risicos_straten import risico
def voeg_bolletje_toe_intern(kaart, latitude, longitude, straatnaam, kleur='black'):
    # Maak een CircleMarker (effen bolletje) met de gegeven coördinaten
    bolletje = folium.CircleMarker(
        location=[latitude, longitude],
        radius=5,  # De grootte van het bolletje
        color=kleur,  # De kleur van het bolletje
        fill=True,  # Vult het bolletje met kleur
        fill_color=kleur,  # De kleur van de vulling
        fill_opacity=1,
        stroke=False,# De transparantie van de vulling
        popup=straatnaam,  # De pop-up die de straatnaam toont
        tooltip=straatnaam
    )
    bolletje.add_to(kaart)

def voeg_bolletje_toe(kaart,gemeente, geselecteerde_straat=None, neerslag_index=None):
    data = {}
    csv_bestand = rf"C:\Users\annab\Documents\P&O 3\website_flask\coordinaten_straten\SAMENVOEG_{gemeente}.csv"
    with open(csv_bestand, mode="r") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            # Haal de gemeente naam en de coördinaten op
            straat = row[reader.fieldnames[0]]
            coordinaten = json.loads(row[reader.fieldnames[1]])  # JSON-string terug omzetten naar een lijst

            # Sla de gegevens op in de dictionary
            data[straat] = [coordinaten]

    g = folium.FeatureGroup(name="Geen risico")
    y = folium.FeatureGroup(name="Weinig risico")
    r = folium.FeatureGroup(name="Veel risico")
    # risicos toevoegen
    data = risico(data, neerslag_index)
 
    # Voeg bolletjes toe aan de kaart
    kleuren = ["green","yellow","red"]
    for straat,coords_risicos in data.items():
        coords = coords_risicos[0]
        risico = coords_risicos[1]
        if len(coords) == 2:
            if straat == geselecteerde_straat:
                if risico > 2000: 
                    kaart = r
                elif risico > 1000:
                    kaart = y
                else: 
                    kaart = g
                voeg_bolletje_toe_intern(kaart, coords[0], coords[1], straat, kleur='rgb(19, 57, 128)')
            else:
                if risico > 2000: 
                    voeg_bolletje_toe_intern(g, coords[0], coords[1], straat, kleur='red')
                elif risico > 1000:
                    voeg_bolletje_toe_intern(y, coords[0], coords[1], straat, kleur='yellow')
                voeg_bolletje_toe_intern(r, coords[0], coords[1], straat, kleur='green')
    # Opslaan van de kaart als een HTML-bestand
    g.add_to(kaart)
    y.add_to(kaart)
    r.add_to(kaart)
    return kaart
