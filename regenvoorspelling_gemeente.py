import HDF_lezer
import csv
import json
paths_geo = [r"C:\Users\annab\Documents\P&O 3", r"C:\Users\jarne\Desktop\KUL 2Bir - Semester 3\P&O3"]
paths_web = [r"C:\Users\annab\Documents\P&O 3", r"C:\Users\jarne\PycharmProjects\KUL Bir - 2e semester\P&O3" ]
i = 0
# 0 = Annabel
# 1 = Jarne

path = paths_web[i] + r'\website_flask\HDF_DAGEN\hdf - 15jul'


###data verzamelen
precip_dag = HDF_lezer.data_lezer(path,True)
###bestand indices openen
# Bestandspad naar het CSV-bestand
csv_bestandsnaam = "gemeenten_met_indices.csv"

# Initialiseer een lege dictionary om de gegevens op te slaan
gemeenten_data = {}

# Lees het CSV-bestand en vul de dictionary
with open(csv_bestandsnaam, mode="r") as csv_file:
    reader = csv.DictReader(csv_file)
    for row in reader:
        # Haal de gemeente naam en de coördinaten op
        gemeente_naam = row["Gemeente"]
        coordinaten = json.loads(row["Indices"])  # JSON-string terug omzetten naar een lijst

        # Sla de gegevens op in de dictionary
        gemeenten_data[gemeente_naam] = coordinaten

print(gemeenten_data)
###regenverzameling
regen_per_gemeente = {}
for gemeente, indices in sorted(gemeenten_data.items()):
    regen = 0
    for index in indices:
        lat = index[0]
        lon = index[1]
        regen_punt = float(precip_dag[lat,lon])
        regen += regen_punt
    #if regen != 0.0:
    regen_per_gemeente[gemeente] = regen


print(regen_per_gemeente)
print(regen_per_gemeente["Hasselt"])
print(regen_per_gemeente["Antwerpen"])