import os
import pysteps
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

def data_lezer(path,dag = True):
    #Locatie van mapje
    hdf_filepath = path
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
         ] = pysteps.io.importers.import_odim_hdf5(f'{hdf_filepath}/{hdf_file}',
                                                   qty=agg_type.upper())
        precipitation = np.append(precipitation, hdf_precipitation)
        timestamps = np.append(timestamps, hdf_timestamp)

    # Reshape qpe array
    n_timesteps = len(hdf_files)
    precipitation = precipitation.reshape((n_timesteps, 700, 700))
    precipitation = np.nan_to_num(precipitation,nan=0.0)
    precip_24h = np.sum(precipitation,axis=0)
    if dag:
        return precip_24h
    else: return precipitation
