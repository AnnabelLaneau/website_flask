import random


def risico(data, neerslag_index):
    for straat,coords_risicos in data.items():
                a = random.randint(0,5000)
                coords_risicos.append(a)
    return data 