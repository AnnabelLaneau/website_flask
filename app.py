from flask import Flask, render_template, request, jsonify, session
import geopandas as gpd
import pandas as pd
import folium
import os
import kaart_vlaanderen
import risicos_berekenen
import risicos_straten
import shutil
import warnings # dit is om die reuzachtige error te onderdukken
from bolletjes_gemeenteniveau import voeg_bolletje_toe
warnings.simplefilter(action='ignore', category=FutureWarning)
# HANDIGE SITES
    # voor folium: https://python-visualization.github.io/folium/latest/index.html

#PAS HIER PATH AAN
paths_geo = [r"C:\Users\annab\Documents\P&O 3", r"C:\Users\jarne\Desktop\KUL 2Bir - Semester 3\P&O3"]
paths_web = [r"C:\Users\annab\Documents\P&O 3", r"C:\Users\jarne\PycharmProjects\KUL Bir - 2e semester\P&O3" ]
i = 0
# 0 = Annabel
# 1 = Jarne

# om Flask webapplicatie te initaliseren: moet hier ALTIJD staan    
app = Flask(__name__)
app.secret_key = 'drup_secret_key_123' 

# Bestanden pad initialiseren
vlaanderen_arrondisementen_path = paths_geo[i] + r"\vlaanderen_arrondisement\Refarr25G10.shp"
vlaanderen_gemeenten_path = paths_geo[i] + r"\vlaanderen_gemeentes\Refgem25G100.shp"
gemeenten_riscios_path = paths_geo[i] + r"\gemeenten_risicos.csv"
arrondisement_risicos_path = paths_geo[i] + r"\arrondisement_risicos_test2.csv"
kaart_html_path = paths_web[i] + r"\website_flask\static/kaarten/kaart_vlaanderen.html"
upload_folder = paths_web[i] +r'\website_flask\upload_regen'
datums_neerslag = [paths_web[i] + r'\website_flask\HDF_DAGEN\hdf - 15jul',
                       paths_web[i] + r'\website_flask\HDF_DAGEN\hdf - 26aug',
                       paths_web[i] + r'\website_flask\HDF_DAGEN\hdf - 28aug'] #data en gegevens-paths voor de 3 neerslagen
 #_______________________________________________________________HOME__________________________________________________________________________________________________
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET' and not request.args.get('action'):
        session.pop('current_risicos', None)
        session.pop('current_rainfall', None)
    #action = 'default' # er zit ergens een fout dat die na herladen die vorige actie toch nog blijft uitvoeren: MOET NOG GEFIXT WORDEN 
    action = request.args.get('action', 'default') #luistert naar acties van website
    gekozen_gemeente = request.args.get('gemeente', None)
    #huidige_gemeenten_risicos = None
    print('actie is:',action)


###############################################GEGEVENS#################################################
    # Laad de shapefiles en CSV:
    #vlaanderen_arrondisementen = gpd.read_file(vlaanderen_arrondisementen_path)
    vlaanderen_gemeenten = gpd.read_file(vlaanderen_gemeenten_path)
    #arrondisement_risicos = pd.read_csv(arrondisement_risicos_path, sep=';')
    # Naar juist coordinaten-systeem zetten om te plotten: 
    if vlaanderen_gemeenten.crs != "EPSG:4326":
        vlaanderen_gemeenten= vlaanderen_gemeenten.to_crs(epsg=4326)

    # Bestanden klaarmaken om door te geven naar Home-pagina: 
    subset_vlaanderen_gemeenten = vlaanderen_gemeenten[['NAAM', 'geometry']]
    subset_vlaanderen_gemeenten.loc[:, 'geometry'] = subset_vlaanderen_gemeenten['geometry'].apply(lambda x: x.__geo_interface__)
                    # Maak een lijst van tuples met (NAAM, GEOMETRIE)
    gemeenten_lijst = [(row['NAAM'], row['geometry']) for _, row in subset_vlaanderen_gemeenten.iterrows()]
    gemeenten_lijst = sorted(gemeenten_lijst, key=lambda x: x[0])



##########################################KAART#############################################################

    # Maken Folium kaart aan en groepen
    m = kaart_vlaanderen.init_map(vlaanderen_gemeenten)
    regen_groep = folium.FeatureGroup(name="Dagelijkse neerslag", overlay=True, control=True, show=False)
    gemeenten_groep = folium.FeatureGroup(name="Gemeenten",overlay=True,control=True,show=False)


    if request.method == 'POST':
        # Controleer of er bestanden zijn geüpload
        # Controleer of er bestanden zijn geüpload
        if 'rainfile' in request.files:
            files = request.files.getlist('rainfile')  # Haal alle bestanden op als lijst
            ##BESTANDEN UPLOADEN
            # Print de lengte van de bestandenlijst voor debugging
            print(f"Aantal geüploade bestanden: {len(files)}")


            if os.path.exists(upload_folder):
                shutil.rmtree(upload_folder)

            for file in files:
                if file:
                    filepath = os.path.join(upload_folder, file.filename)
        
                    # Zorg ervoor dat de map bestaat door de directory-structuur aan te maken
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    file.save(filepath)
                    print(f"Bestand opgeslagen: {filepath}")

            ##KAARTJE MAKEN
            inhoud_upload_regen = os.listdir(upload_folder)
            uploaded_data = upload_folder + "/" + inhoud_upload_regen[0]
            datums_neerslag.append(uploaded_data)

    if action == 'rainfall1':
            huidige_gemeenten_risicos = risicos_berekenen.risico(vlaanderen_gemeenten,datums_neerslag[0])
            session['current_rainfall'] = 0
            session.modified = True
            m = kaart_vlaanderen.init_map(vlaanderen_gemeenten)
            m = kaart_vlaanderen.add_rainfall_layer_h(m,datums_neerslag[0])  #KAN NIET IN EEN FEATURE GROEP WANT DAN WERKT HET NIET, naamgeving in de heatmap functie zelf (kaart_vlaanderen)
            gemeenten_groep2 = folium.FeatureGroup(name="Gemeenten", overlay=True, control=False, show=True)
            gemeenten_groep2 = kaart_vlaanderen.add_gemeenten_layer(gemeenten_groep2, vlaanderen_gemeenten,0.3, huidige_gemeenten_risicos) #vervaging nodig om wolkjes te zien
            gemeenten_groep2.add_to(m)
            regen_groep = kaart_vlaanderen.add_rainfall_layer_d(regen_groep, datums_neerslag[0]) #dagelijkse neerslag
            regen_groep.add_to(m)
        
            folium.LayerControl().add_to(m) #hiermee kan je verschillende lagen aan en uitzetten (show=F/T om ze op het begin uit of aan te zetten)
            m.save(kaart_html_path)
            iframe_html = f'<iframe src="/static/kaarten/kaart_vlaanderen.html" width="100%" height="100%"></iframe >'
            print('iframe gemaakt')
            return iframe_html  # Stuur de iframe HTML terug voor de kaart

    elif action == 'rainfall2':
            huidige_gemeenten_risicos = risicos_berekenen.risico(vlaanderen_gemeenten,datums_neerslag[1])
            session['current_rainfall'] = 1
            session.modified = True
            m = kaart_vlaanderen.init_map(vlaanderen_gemeenten)
            m = kaart_vlaanderen.add_rainfall_layer_h(m, datums_neerslag[1])  # KAN NIET IN EEN FEATURE GROEP WANT DAN WERKT HET NIET
            gemeenten_groep2 = folium.FeatureGroup(name="Gemeenten", overlay=True, control=False, show=True)
            gemeenten_groep2 = kaart_vlaanderen.add_gemeenten_layer(gemeenten_groep2, vlaanderen_gemeenten,0.3, huidige_gemeenten_risicos)  # vervaging nodig om wolkjes te zien
            regen_groep = kaart_vlaanderen.add_rainfall_layer_d(regen_groep,datums_neerslag[1])
            regen_groep.add_to(m)
            gemeenten_groep2.add_to(m)
            folium.LayerControl().add_to(m)
            m.save(kaart_html_path)
            print("Home route - setting session:", session['current_rainfall'])
            iframe_html = f'<iframe src="/static/kaarten/kaart_vlaanderen.html" width="100%" height="100%"></iframe >'
            print('inframe gemaakt')
            return iframe_html  # Stuur de iframe HTML terug voor de kaart
    elif action == 'rainfall3':
            huidige_gemeenten_risicos = risicos_berekenen.risico(vlaanderen_gemeenten,datums_neerslag[2])
            session['current_rainfall'] = 2
            session.modified = True
            m = kaart_vlaanderen.init_map(vlaanderen_gemeenten)
            m = kaart_vlaanderen.add_rainfall_layer_h(m, datums_neerslag[2])  # KAN NIET IN EEN FEATURE GROEP WANT DAN WERKT HET NIET
            gemeenten_groep2 = folium.FeatureGroup(name="Gemeenten", overlay=True, control=False, show=True)
            gemeenten_groep2 = kaart_vlaanderen.add_gemeenten_layer(gemeenten_groep2, vlaanderen_gemeenten,0.3, huidige_gemeenten_risicos)  # vervaging nodig om wolkjes te zien
            regen_groep = kaart_vlaanderen.add_rainfall_layer_d(regen_groep, datums_neerslag[2])
            regen_groep.add_to(m)
            gemeenten_groep2.add_to(m)
            folium.LayerControl().add_to(m)
            m.save(kaart_html_path)
            iframe_html = f'<iframe src="/static/kaarten/kaart_vlaanderen.html" width="100%" height="100%"></iframe >'
            print('inframe gemaakt')
            return iframe_html  # Stuur de iframe HTML terug voor de kaart
    elif action == 'rainfallupload': 
            uploaded_data = datums_neerslag[3]
            session['current_rainfall'] = 3
            session.modified = True
            gemeenten_risicos = risicos_berekenen.risico(vlaanderen_gemeenten, uploaded_data)
            m = kaart_vlaanderen.init_map(vlaanderen_gemeenten)
            m = kaart_vlaanderen.add_rainfall_layer_h(m, uploaded_data)  # KAN NIET IN EEN FEATURE GROEP WANT DAN WERKT HET NIET
            gemeenten_groep2 = folium.FeatureGroup(name="Gemeenten", overlay=True, control=True, show=True)
            gemeenten_groep2 = kaart_vlaanderen.add_gemeenten_layer(gemeenten_groep2, vlaanderen_gemeenten, 0.3,
                                                                    gemeenten_risicos)  # vervaging nodig om wolkjes te zien
            regen_groep = kaart_vlaanderen.add_rainfall_layer_d(regen_groep, uploaded_data)
            regen_groep.add_to(m)
            gemeenten_groep2.add_to(m)
            folium.LayerControl().add_to(m)
            m.save(kaart_html_path)
            iframe_html = f'<iframe src="/static/kaarten/kaart_vlaanderen.html" width="100%" height="100%"></iframe >'
            print('inframe gemaakt')
            return iframe_html
    
    if action == 'select_gemeente':
            gekozen_gemeente = request.args.get('gemeente')
            session['current_gemeente'] = gekozen_gemeente
            hele_lijst = kaart_vlaanderen.straten_per_gemeente()
            straten_lijst = hele_lijst[gekozen_gemeente]
            print(straten_lijst)
            print(f'Gekozen gemeente: {gekozen_gemeente}')


            neerslag_index = session['current_rainfall']
            current_risicos = risicos_berekenen.risico(vlaanderen_gemeenten,datums_neerslag[neerslag_index])

            m = kaart_vlaanderen.init_map(vlaanderen_gemeenten)
            if current_risicos is not None:
                m = kaart_vlaanderen.highlight_selected_gemeente(m, vlaanderen_gemeenten, gekozen_gemeente, current_risicos)
            else:
                m = kaart_vlaanderen.highlight_selected_gemeente(m, vlaanderen_gemeenten, gekozen_gemeente)
            m.save(kaart_html_path)
            iframe_html = f'<iframe src="/gemeente/{gekozen_gemeente}" width="90%" height="100%"></iframe>'
            print(iframe_html)
            return jsonify({
                'kaart_vlaanderen_html': f'<iframe src="/static/kaarten/kaart_vlaanderen.html" width="100%" height="100%"></iframe >' ,
                'gemeente_html': iframe_html,
                'lijst_van_straten': straten_lijst,
            })
    if action == 'select_straat':  
        geselecteerde_straat = request.args.get('straat')
        print('er is een straat gekozen')
        # Get the gemeente name from the request parameters
        gekozen_gemeente = session['current_gemeente']
        print('gekozen gemeente', gekozen_gemeente)
        if gekozen_gemeente:
            iframe_html = f'<iframe src="/gemeente/{gekozen_gemeente}?straat={geselecteerde_straat}" width="90%" height="100%"></iframe>'
            return jsonify({
                'gemeente_html': iframe_html,
            })
        else:
            return jsonify({'error': 'No gemeente specified'})

    m.save(kaart_html_path)
    return render_template('home.html', title='Home', vlaanderen_gemeenten=gemeenten_lijst)


#_____________________________________________________________________________GEMEENTE_________________________________________________________________________________________
@app.route('/gemeente/<string:gemeente_naam>')
def gemeente(gemeente_naam):
    # Laad de shapefile voor gemeenten
    vlaanderen_gemeenten = gpd.read_file(vlaanderen_gemeenten_path)

    if vlaanderen_gemeenten.crs != "EPSG:4326":
        vlaanderen_gemeenten= vlaanderen_gemeenten.to_crs(epsg=4326)

    # Filter de geselecteerde gemeente
    geselecteerde_gemeente = vlaanderen_gemeenten[vlaanderen_gemeenten['NAAM'] == gemeente_naam]
    geselecteerde_straat = request.args.get('straat', None)


    # Controleer of de gemeente bestaat
    if not geselecteerde_gemeente.empty:
        # Haal de geometrie en coördinaten van de geselecteerde gemeente op
        gemeente_geo = geselecteerde_gemeente.geometry.values[0]

        bounds = gemeente_geo.bounds  
        bounds_with_padding = [
            [bounds[1],bounds[0] ],
            [bounds[3], bounds[2]]]
        
        gemeente_centroid = gemeente_geo.centroid
        gemeente_lat = gemeente_centroid.y
        gemeente_lon = gemeente_centroid.x
        print('Session contents:', session)
        print(session['current_rainfall'])
        #neerslag nemen
        if 'current_rainfall' in session:
                neerslag_index = session['current_rainfall']
                # Maak een Folium-kaart voor de geselecteerde gemeente
        m_gemeente = folium.Map(location=[gemeente_lat, gemeente_lon], tiles='OpenStreetMap')
        m_gemeente = voeg_bolletje_toe(m_gemeente,str(gemeente_naam), geselecteerde_straat, neerslag_index)
        folium.GeoJson(
            gemeente_geo,  # De geometrie van de gemeente
            style_function=lambda feature: {
                'color': 'black',  # Kleur van de omtrek
                'weight': 2,      # Dikte van de omtrek
                'fillColor': 'none',
            }
        ).add_to(m_gemeente)

        m_gemeente.fit_bounds(bounds_with_padding)

        # Sla de gemeente kaart op
        gemeente_html_path = os.path.join('static','kaarten', f'kaart_{gemeente_naam}.html')
        os.makedirs(os.path.dirname(gemeente_html_path), exist_ok=True)

        print(f'Saving gemeente map to {gemeente_html_path}')
        gemeente_html_path_doorsturen = os.path.join('static','kaarten', f'kaart_{gemeente_naam}.html')
        m_gemeente.save(gemeente_html_path)

        return render_template('gemeente.html', gemeente=gemeente_naam, kaart_path=gemeente_html_path_doorsturen)
    else:
        print(f'Gemeente {gemeente_naam} niet gevonden.')
        return "Gemeente niet gevonden.", 404
 

 #_____________________________________________________________________________________ABOUT_____________________________________________________________________________________
@app.route('/about')  # Route voor de About Us-pagina
def about():
    return render_template('about.html', title='About Us')

#______________________________________________________________________________________MAATREGELINGEN________________________________________________________________________________
@app.route('/maatregelingen')  # Route voor de About Us-pagina
def maatregelingen():
    return render_template('maatregelingen.html', title='Maatregelingen')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
# dit zorgt dat bestand runt 
# debug=True: activeert de debug-modus, wat betekent dat de server automatisch opnieuw opstart als je wijzigingen aanbrengt in de code. 



