import os
import pandas as pd
from recombee_api_client.api_client import RecombeeClient, Region
from recombee_api_client.api_requests import AddItemProperty, ListItemProperties
from recombee_api_client.exceptions import APIException

# TODO 1: Configurare credentiale Recombee
# Introduceti datele din contul vostru (Settings -> API Logins in Recombee Admin UI)
DB_NAME = 'mateidragusin-dev'
PRIVATE_TOKEN = os.environ['RECOMBEE_TOKEN']
REGION = Region.EU_WEST  # Schimbati cu 'us-west' sau regiunea potrivita daca este cazul

# Initializarea clientului Recombee
client = RecombeeClient(DB_NAME, PRIVATE_TOKEN, region=REGION)

# TODO 2: Configurare dataset propriu
# Descarcati un dataset (CSV) de pe Kaggle/data.world (100-10K de intrari)
# Urcati fisierul in acelasi folder cu acest script si setati numele in variabila de mai jos
PATH_DATASET = 'imdb_top_1000.csv' 

# TODO 3: Definirea schemei de date (minim 3 proprietati)
# Adaptati aceasta lista in functie de coloanele din dataset-ul ales
# Tipurile de date suportate de Recombee includ: 'string', 'int', 'double', 'boolean', 'timestamp'
# Ex.: Pentru filme: titlu (string), an (int), rating (double)
PROPRIETATI_CATALOG = [
    {"name": "title", "type": "string"},
    {"name": "released_year", "type": "int"},
    {"name": "runtime", "type": "int"},
    {"name": "genre", "type": "set"},
    {"name": "imdb_rating", "type": "double"},
    {"name": "meta_score", "type": "double"},
    {"name": "no_of_votes", "type": "int"},
    {"name": "director", "type": "string"},
    {"name": "overview", "type": "string"},
    {"name": "gross", "type": "int"},
]


def load_dataset():
    """Functie helper care citeste si verifica dataset-ul"""
    try:
        df = pd.read_csv(PATH_DATASET)
        total_randuri = len(df)
        print(f"Dataset incarcat cu succes! Total randuri: {total_randuri}")
        
        # Verificare numar de randuri (100 - 10K)
        if total_randuri < 100:
            print("ATENTIE: Dataset-ul are sub 100 de produse!")
        elif total_randuri > 10 * 1000:
            print("ATENTIE: Dataset-ul este prea mare! Limitati-l la primele 10K randuri.")
            
        print("\nPreview primele 3 randuri:")
        print(df.head(3))
        print("-" * 50)
        return df
    except FileNotFoundError:
        print(f"Eroare: Fisierul '{PATH_DATASET}' nu a fost gasit!")
        return None

def set_properties():
    """Functie care trimite structura coloanelor catre Recombee"""
    print(f"\nIncepe definirea proprietatilor pentru baza de date: '{DB_NAME}'...")
    
    for prop in PROPRIETATI_CATALOG:
        # Validare nume proprietati valide
        if "nume_proprietate" in prop["name"]:
            print("Eroare: Trebuie sa schimbati 'nume_proprietate_x' cu denumirile reale din coloanele fisierul vostru!")
            continue
            
        try:
            # Request API Recombee pentru adaugarea proprietatii (echivalentul adaugarii unei coloane intr-un tabel)
            client.send(AddItemProperty(prop["name"], prop["type"]))
            print(f"Proprietatea '{prop['name']}' ({prop['type']}) a fost adaugata cu succes.")
        except APIException as e:
            # Recombee returnează eroare daca proprietatea a fost deja definita la o rulare anterioara
            if "already exists" in str(e).lower():
                print(f"Proprietatea '{prop['name']}' exista deja in Recombee.")
            else:
                print(f"Eroare API la proprietatea '{prop['name']}': {e}")

def verify():
    """Interogheaza API-ul pentru a lista toate proprietatile active dsin cont"""
    print("Se verifica structura finala din Recombee Admin UI...")
    try:
        atribute_active = client.send(ListItemProperties())
        print("Proprietatile configurate in acest moment in baza ta de date:")
        for atribute in atribute_active:
            print(f"- {atribute['name']} => tip de date: {atribute['type']}")
    except APIException as e:
        print(f"Nu s-a putut efectua verificarea. Detalii eroare: {e}")

if __name__ == "__main__":
    # Verificam daca fisierul CSV local se citeste corect
    dataset_ok = load_dataset()
    
    if dataset_ok is not None:
        # Trimitem proprietatile catre Recombee prin API
        set_properties()
        
        # Listam ce s-a salvat in baza de date pentru confirmare
        verify()
