import random


def risico(data, neerslag_index):
    for straat,coords_risicos in data.items():
                a = random.randint(0,2000)
                coords_risicos.append(a)
    print(data)
    return data 