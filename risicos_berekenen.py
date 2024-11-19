import geopandas as gpd
import pandas as pd

paths_geo = [r"C:\Users\annab\Documents\P&O 3", r"C:\Users\jarne\Desktop\KUL 2Bir - Semester 3\P&O3"]
paths_web = [r"C:\Users\annab\Documents\P&O 3", r"C:\Users\jarne\PycharmProjects\KUL Bir - 2e semester\P&O3" ]
i = 0
# 0 = Annabel
# 1 = Jarne

def risico(vlaanderen_gemeenten,neerslagdata):
    gemeenten_riscios_path = paths_geo[i] + r"\gemeenten_risicos.csv"
    gemeenten_risicos = pd.read_csv(gemeenten_riscios_path, sep=';')

    return gemeenten_risicos